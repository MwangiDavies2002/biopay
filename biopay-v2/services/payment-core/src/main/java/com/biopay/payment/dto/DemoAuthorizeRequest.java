package com.biopay.payment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record DemoAuthorizeRequest(@NotBlank @Size(max = 64) String deviceId, boolean liveness) {}
