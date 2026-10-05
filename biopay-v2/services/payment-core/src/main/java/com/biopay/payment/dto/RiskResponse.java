package com.biopay.payment.dto;

public record RiskResponse(double riskScore, String decision, String reason) {}
