package portfolio_spring.v1.security;

import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import portfolio_spring.v1.model.Administrator;
import portfolio_spring.v1.repository.AdministratorRepository;

import java.util.ArrayList;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    private final AdministratorRepository administratorRepository;

    public CustomUserDetailsService(AdministratorRepository administratorRepository) {
        this.administratorRepository = administratorRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        // Buscamos en PostgreSQL
        Administrator admin = administratorRepository.findByUsername(username)
                .orElseThrow(() -> new UsernameNotFoundException("Administrador no encontrado: " + username));

        // Traducimos al objeto User de Spring Security (asumimos roles vacíos con ArrayList)
        return new User(admin.getUsername(), admin.getPasswordHash(), new ArrayList<>());
    }
}
