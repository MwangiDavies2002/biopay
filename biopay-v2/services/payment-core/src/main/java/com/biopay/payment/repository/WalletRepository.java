package com.biopay.payment.repository;

import com.biopay.payment.model.Wallet;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;
import java.util.Optional;

public interface WalletRepository extends JpaRepository<Wallet, String> {
    Optional<Wallet> findByOwnerIdAndCurrency(String ownerId, String currency);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select w from Wallet w where w.ownerId = :ownerId and w.currency = :currency")
    Optional<Wallet> lockByOwnerIdAndCurrency(@Param("ownerId") String ownerId, @Param("currency") String currency);
}
