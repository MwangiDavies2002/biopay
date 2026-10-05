package com.biopay.payment.controller;

import com.biopay.payment.dto.*;
import com.biopay.payment.service.PaymentService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = {"http://localhost:3000", "http://localhost:3001"})
public class PaymentController {
    private final PaymentService service;

    public PaymentController(PaymentService service) { this.service = service; }

    @GetMapping("/health")
    public Map<String, Object> health() { return Map.of("status", "ok", "service", "payment-core"); }

    @PostMapping("/payment-requests")
    public PaymentResponse create(@Valid @RequestBody CreatePaymentRequest request) { return service.create(request); }

    @GetMapping("/payment-requests/{id}")
    public PaymentResponse get(@PathVariable String id) { return service.get(id); }

    @PostMapping("/payment-requests/{id}/demo-authorize")
    public PaymentResponse demoAuthorize(@PathVariable String id, @Valid @RequestBody DemoAuthorizeRequest request) {
        return service.demoAuthorize(id, request);
    }

    @GetMapping("/wallets/{ownerId}")
    public WalletResponse wallet(@PathVariable String ownerId) { return service.wallet(ownerId); }

    @ExceptionHandler({IllegalArgumentException.class, IllegalStateException.class})
    public ResponseEntity<Map<String, String>> handle(RuntimeException ex) {
        return ResponseEntity.badRequest().body(Map.of("error", ex.getMessage()));
    }
}
