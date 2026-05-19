package portfolio_spring.v1.repository;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import portfolio_spring.v1.model.KnowledgeEntry;
import java.util.List;

public interface KnowledgeEntryRepository extends JpaRepository<KnowledgeEntry, Integer> {

    @EntityGraph(attributePaths = {"entryTechnologies.technology"})
    List<KnowledgeEntry> findAll();
}
