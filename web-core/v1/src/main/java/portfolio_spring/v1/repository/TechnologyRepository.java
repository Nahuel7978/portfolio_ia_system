package portfolio_spring.v1.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import portfolio_spring.v1.model.Technology;

public interface TechnologyRepository extends JpaRepository<Technology, Integer> {
    boolean existsByName(String name);
}
