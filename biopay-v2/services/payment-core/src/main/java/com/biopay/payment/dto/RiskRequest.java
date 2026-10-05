package com.biopay.payment.dto;

import java.math.BigDecimal;

public record RiskRequest(
        String paymentId,
        String payerUserId,
        String merchantId,
        String deviceId,
        BigDecimal amount,
        String currency,
        boolean liveness,
        int recentAttemptCount
) {}
