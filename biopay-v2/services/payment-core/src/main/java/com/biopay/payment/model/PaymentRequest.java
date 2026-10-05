package com.biopay.payment.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "payment_request")
public class PaymentRequest {
    @Id
    private String id;
    @Column(name = "payer_user_id", nullable = false)
    private String payerUserId;
    @Column(name = "merchant_id", nullable = false)
    private String merchantId;
    @Column(nullable = false, precision = 19, scale = 4)
    private BigDecimal amount;
    @Column(nullable = false, length = 3, columnDefinition = "CHAR(3)")
    private String currency;
    @Column(nullable = false)
    private String status;
    @Column(name = "nonce_hash", nullable = false)
    private String nonceHash;
    @Column(name = "expires_at", nullable = false)
    private Instant expiresAt;
    @Column(name = "approved_at")
    private Instant approvedAt;
    @Column(name = "created_at", insertable = false, updatable = false)
    private Instant createdAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getPayerUserId() { return payerUserId; }
    public void setPayerUserId(String payerUserId) { this.payerUserId = payerUserId; }
    public String getMerchantId() { return merchantId; }
    public void setMerchantId(String merchantId) { this.merchantId = merchantId; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getNonceHash() { return nonceHash; }
    public void setNonceHash(String nonceHash) { this.nonceHash = nonceHash; }
    public Instant getExpiresAt() { return expiresAt; }
    public void setExpiresAt(Instant expiresAt) { this.expiresAt = expiresAt; }
    public Instant getApprovedAt() { return approvedAt; }
    public void setApprovedAt(Instant approvedAt) { this.approvedAt = approvedAt; }
    public Instant getCreatedAt() { return createdAt; }
}
