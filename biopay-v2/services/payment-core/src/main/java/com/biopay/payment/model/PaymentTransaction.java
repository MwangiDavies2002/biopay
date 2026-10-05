package com.biopay.payment.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "payment_transaction")
public class PaymentTransaction {
    @Id
    private String id;
    @Column(name = "payment_request_id", nullable = false, unique = true)
    private String paymentRequestId;
    @Column(nullable = false)
    private String status;
    @Column(name = "risk_score", nullable = false, precision = 8, scale = 6)
    private BigDecimal riskScore;
    @Column(name = "created_at", insertable = false, updatable = false)
    private Instant createdAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getPaymentRequestId() { return paymentRequestId; }
    public void setPaymentRequestId(String paymentRequestId) { this.paymentRequestId = paymentRequestId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public BigDecimal getRiskScore() { return riskScore; }
    public void setRiskScore(BigDecimal riskScore) { this.riskScore = riskScore; }
}
