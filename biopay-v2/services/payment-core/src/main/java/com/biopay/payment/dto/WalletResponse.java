package com.biopay.payment.dto;

import java.math.BigDecimal;

public record WalletResponse(String walletId, String ownerId, String currency, BigDecimal balance) {}
