package portfolio_spring.v1.repository;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import portfolio_spring.v1.model.Administrator;

public interface AdministratorRepository extends JpaRepository<Administrator, Integer> {

    Optional<Administrator> findByUsername(String username);

}
