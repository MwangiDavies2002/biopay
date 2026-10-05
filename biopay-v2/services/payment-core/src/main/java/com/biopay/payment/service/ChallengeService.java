package com.biopay.payment.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.time.Duration;
import java.util.Base64;

@Service
public class ChallengeService {
    private final StringRedisTemplate redis;
    private final SecureRandom random = new SecureRandom();
    private final long ttlSeconds;

    public ChallengeService(StringRedisTemplate redis,
                            @Value("${biopay.challenge-ttl-seconds:90}") long ttlSeconds) {
        this.redis = redis;
        this.ttlSeconds = ttlSeconds;
    }

    public String issue(String paymentId) {
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        String challenge = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
        redis.opsForValue().set(key(paymentId), challenge, Duration.ofSeconds(ttlSeconds));
        return challenge;
    }

    public boolean exists(String paymentId) {
        return Boolean.TRUE.equals(redis.hasKey(key(paymentId)));
    }

    public void consume(String paymentId) {
        redis.delete(key(paymentId));
    }

    private String key(String paymentId) { return "payment-challenge:" + paymentId; }
}
