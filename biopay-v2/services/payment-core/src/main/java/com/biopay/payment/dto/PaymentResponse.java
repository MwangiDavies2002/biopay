package com.biopay.payment.dto;

import java.math.BigDecimal;
import java.time.Instant;

public record PaymentResponse(
        String id,
        String payerUserId,
        String merchantId,
        BigDecimal amount,
        String currency,
        String status,
        String challenge,
        Instant expiresAt
) {}
