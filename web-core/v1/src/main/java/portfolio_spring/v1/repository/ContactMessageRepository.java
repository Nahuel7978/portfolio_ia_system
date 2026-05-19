package portfolio_spring.v1.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import portfolio_spring.v1.model.ContactMessage;

public interface ContactMessageRepository extends JpaRepository<ContactMessage, Integer> {
}
