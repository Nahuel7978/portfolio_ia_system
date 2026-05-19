package portfolio_spring.v1.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class JwtRequestFilter extends OncePerRequestFilter {

    private final CustomUserDetailsService userDetailsService;
    private final JwtTokenUtil jwtTokenUtil;

    public JwtRequestFilter(CustomUserDetailsService userDetailsService, JwtTokenUtil jwtTokenUtil) {
        this.userDetailsService = userDetailsService;
        this.jwtTokenUtil = jwtTokenUtil;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {

        // 1. Obtener la cabecera "Authorization"
        final String requestTokenHeader = request.getHeader("Authorization");

        String username = null;
        String jwtToken = null;

        // 2. Extraer el token si la cabecera es correcta
        if (requestTokenHeader != null && requestTokenHeader.startsWith("Bearer ")) {
            jwtToken = requestTokenHeader.substring(7); // Quitar "Bearer "
            try {
                username = jwtTokenUtil.getUsernameFromToken(jwtToken);
            } catch (Exception e) {
                logger.error("Error al extraer o validar el JWT: " + e.getMessage());
            }
        }

        // 3. Si tenemos usuario pero no está autenticado aún en el contexto
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {

            // Cargar datos de la BD
            UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);

            // Validar token vs usuario
            if (jwtTokenUtil.validateToken(jwtToken, userDetails)) {
                // Autenticar manualmente
                UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());

                auth.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

                // Establecer la autenticación en Spring Security
                SecurityContextHolder.getContext().setAuthentication(auth);
            }
        }

        // 4. Continuar con la cadena de filtros de la petición
        chain.doFilter(request, response);
    }
}
