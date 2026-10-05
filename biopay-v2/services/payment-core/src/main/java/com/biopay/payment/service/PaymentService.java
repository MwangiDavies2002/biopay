package com.biopay.payment.service;

import com.biopay.payment.dto.*;
import com.biopay.payment.model.*;
import com.biopay.payment.repository.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.HexFormat;
import java.util.UUID;

@Service
public class PaymentService {
    private final PaymentRequestRepository payments;
    private final PaymentTransactionRepository transactions;
    private final LedgerEntryRepository ledger;
    private final WalletRepository wallets;
    private final ChallengeService challenges;
    private final RiskClient riskClient;
    private final boolean demoMode;
    private final long ttlSeconds;
    private final JdbcTemplate jdbc;

    public PaymentService(PaymentRequestRepository payments,
                          PaymentTransactionRepository transactions,
                          LedgerEntryRepository ledger,
                          WalletRepository wallets,
                          ChallengeService challenges,
                          RiskClient riskClient,
                          JdbcTemplate jdbc,
                          @Value("${biopay.demo-mode:false}") boolean demoMode,
                          @Value("${biopay.challenge-ttl-seconds:90}") long ttlSeconds) {
        this.payments = payments;
        this.transactions = transactions;
        this.ledger = ledger;
        this.wallets = wallets;
        this.challenges = challenges;
        this.riskClient = riskClient;
        this.jdbc = jdbc;
        this.demoMode = demoMode;
        this.ttlSeconds = ttlSeconds;
    }

    @Transactional
    public PaymentResponse create(CreatePaymentRequest request) {
        Wallet payer = wallets.findByOwnerIdAndCurrency(request.payerUserId(), request.currency())
                .orElseThrow(() -> new IllegalArgumentException("Payer wallet not found for this currency"));
        Wallet merchant = wallets.findByOwnerIdAndCurrency(request.merchantId(), request.currency())
                .orElseThrow(() -> new IllegalArgumentException("Merchant wallet not found for this currency"));
        if (!"USER".equals(payer.getOwnerType()) || !"MERCHANT".equals(merchant.getOwnerType())) {
            throw new IllegalArgumentException("Invalid payer or merchant identity");
        }
        String id = "PAY-" + UUID.randomUUID();
        String challenge = challenges.issue(id);
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override public void afterCompletion(int status) {
                if (status != STATUS_COMMITTED) challenges.consume(id);
            }
        });

        PaymentRequest p = new PaymentRequest();
        p.setId(id);
        p.setPayerUserId(request.payerUserId());
        p.setMerchantId(request.merchantId());
        p.setAmount(request.amount());
        p.setCurrency(request.currency());
        p.setStatus("PENDING");
        p.setNonceHash(sha256(challenge));
        p.setExpiresAt(Instant.now().plus(ttlSeconds, ChronoUnit.SECONDS));
        payments.save(p);
        return toResponse(p, challenge);
    }

    public PaymentResponse get(String id) {
        PaymentRequest p = payments.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Payment not found"));
        return toResponse(p, null);
    }

    @Transactional(noRollbackFor = PaymentRejectedException.class)
    public PaymentResponse demoAuthorize(String paymentId, DemoAuthorizeRequest auth) {
        if (!demoMode) throw new IllegalStateException("Demo authorization is disabled");

        PaymentRequest p = payments.lockById(paymentId).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Payment not found"));
        if (!"PENDING".equals(p.getStatus())) throw new PaymentRejectedException("Payment is not pending");
        if (Instant.now().isAfter(p.getExpiresAt())) {
            p.setStatus("EXPIRED");
            throw new PaymentRejectedException("Payment request expired");
        }
        if (!challenges.exists(paymentId)) throw new IllegalStateException("Challenge missing or already consumed");
        if (!auth.liveness()) throw new IllegalStateException("Liveness check failed");
        Integer deviceCount = jdbc.queryForObject(
                "select count(*) from registered_device where id = ? and user_id = ? and status = 'ACTIVE'",
                Integer.class, auth.deviceId(), p.getPayerUserId());
        if (deviceCount == null || deviceCount != 1) throw new IllegalArgumentException("Device is not registered to this payer");

        RiskResponse risk = riskClient.score(new RiskRequest(
                p.getId(), p.getPayerUserId(), p.getMerchantId(), auth.deviceId(),
                p.getAmount(), p.getCurrency(), auth.liveness(), 0));
        if (risk == null || !"APPROVE".equals(risk.decision())) {
            throw new IllegalStateException("Risk engine decision: " + (risk == null ? "NO_RESPONSE" : risk.decision()));
        }

        Wallet payer = wallets.lockByOwnerIdAndCurrency(p.getPayerUserId(), p.getCurrency())
                .orElseThrow(() -> new IllegalStateException("Payer wallet not found"));
        Wallet merchant = wallets.lockByOwnerIdAndCurrency(p.getMerchantId(), p.getCurrency())
                .orElseThrow(() -> new IllegalStateException("Merchant wallet not found"));

        if (payer.getBalance().compareTo(p.getAmount()) < 0) throw new IllegalStateException("Insufficient funds");

        payer.setBalance(payer.getBalance().subtract(p.getAmount()));
        merchant.setBalance(merchant.getBalance().add(p.getAmount()));
        wallets.save(payer);
        wallets.save(merchant);

        String txId = "TX-" + UUID.randomUUID();
        PaymentTransaction tx = new PaymentTransaction();
        tx.setId(txId);
        tx.setPaymentRequestId(p.getId());
        tx.setStatus("POSTED");
        tx.setRiskScore(BigDecimal.valueOf(risk.riskScore()));
        transactions.saveAndFlush(tx);

        ledger.save(entry(txId, payer.getId(), "DEBIT", p.getAmount(), p.getCurrency()));
        ledger.save(entry(txId, merchant.getId(), "CREDIT", p.getAmount(), p.getCurrency()));

        p.setStatus("APPROVED");
        p.setApprovedAt(Instant.now());
        payments.save(p);
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override public void afterCommit() { challenges.consume(paymentId); }
        });
        return toResponse(p, null);
    }

    public WalletResponse wallet(String ownerId) {
        Wallet w = wallets.findByOwnerIdAndCurrency(ownerId, "KES")
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Wallet not found"));
        return new WalletResponse(w.getId(), w.getOwnerId(), w.getCurrency(), w.getBalance());
    }

    private LedgerEntry entry(String tx, String wallet, String direction, BigDecimal amount, String currency) {
        LedgerEntry e = new LedgerEntry();
        e.setTransactionId(tx); e.setWalletId(wallet); e.setDirection(direction); e.setAmount(amount); e.setCurrency(currency);
        return e;
    }

    private PaymentResponse toResponse(PaymentRequest p, String challenge) {
        return new PaymentResponse(p.getId(), p.getPayerUserId(), p.getMerchantId(), p.getAmount(), p.getCurrency(), p.getStatus(), challenge, p.getExpiresAt());
    }

    private String sha256(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("Unable to hash challenge", e);
        }
    }
}
