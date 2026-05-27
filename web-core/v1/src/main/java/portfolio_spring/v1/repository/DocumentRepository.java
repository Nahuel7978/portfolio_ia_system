package portfolio_spring.v1.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import portfolio_spring.v1.model.Document;
import java.util.List;
import java.util.Optional;

public interface DocumentRepository extends JpaRepository<Document, Integer> {
    List<Document> findByEntryId(Integer entryId);
    List<Document> findBySyncStatus(String syncStatus);
    List<Document> findBySyncStatusIn(List<String> statuses);

    @Modifying
    @Query("DELETE FROM Document d WHERE d.entry.id = :entryId")
    void deleteByEntryId(@Param("entryId") Integer entryId);

 // Para validar si ya existe un summary
    boolean existsByEntryIdAndDocType(Integer entryId, String docType);

    // Para recuperar el summary en el endpoint público
    Optional<Document> findFirstByEntryIdAndDocType(Integer entryId, String docType);
}
