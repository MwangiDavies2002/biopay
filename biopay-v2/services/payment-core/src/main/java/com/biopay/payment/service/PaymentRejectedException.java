package com.biopay.payment.service;

public class PaymentRejectedException extends IllegalStateException {
    public PaymentRejectedException(String message) { super(message); }
}
