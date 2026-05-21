package portfolio_spring.v1.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import portfolio_spring.v1.model.Document;
import java.util.List;

public interface DocumentRepository extends JpaRepository<Document, Integer> {
    List<Document> findByEntryId(Integer entryId);
    List<Document> findBySyncStatus(String syncStatus);
}
