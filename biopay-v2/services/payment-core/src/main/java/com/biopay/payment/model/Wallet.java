package com.biopay.payment.model;

import jakarta.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "wallet")
public class Wallet {
    @Id
    private String id;
    @Column(name = "owner_type", nullable = false)
    private String ownerType;
    @Column(name = "owner_id", nullable = false)
    private String ownerId;
    @Column(nullable = false, length = 3, columnDefinition = "CHAR(3)")
    private String currency;
    @Column(nullable = false, precision = 19, scale = 4)
    private BigDecimal balance;
    @Version
    private long version;

    public String getId() { return id; }
    public String getOwnerType() { return ownerType; }
    public String getOwnerId() { return ownerId; }
    public String getCurrency() { return currency; }
    public BigDecimal getBalance() { return balance; }
    public void setBalance(BigDecimal balance) { this.balance = balance; }
}
