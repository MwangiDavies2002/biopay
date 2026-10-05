package com.biopay.payment.model;

import jakarta.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "ledger_entry")
public class LedgerEntry {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "transaction_id", nullable = false)
    private String transactionId;
    @Column(name = "wallet_id", nullable = false)
    private String walletId;
    @Column(nullable = false)
    private String direction;
    @Column(nullable = false, precision = 19, scale = 4)
    private BigDecimal amount;
    @Column(nullable = false, length = 3, columnDefinition = "CHAR(3)")
    private String currency;

    public void setTransactionId(String transactionId) { this.transactionId = transactionId; }
    public void setWalletId(String walletId) { this.walletId = walletId; }
    public void setDirection(String direction) { this.direction = direction; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public void setCurrency(String currency) { this.currency = currency; }
}
