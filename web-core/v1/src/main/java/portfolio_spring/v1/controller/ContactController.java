package portfolio_spring.v1.controller;

import io.github.bucket4j.Bucket;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import portfolio_spring.v1.dto.ContactRequestDTO;
import portfolio_spring.v1.security.RateLimitingService;
import portfolio_spring.v1.service.ContactService;

@RestController
@RequestMapping("/api/v1/public/contact")
public class ContactController {

    private final ContactService contactService;
    private final RateLimitingService rateLimitingService;

    public ContactController(ContactService contactService, RateLimitingService rateLimitingService) {
        this.contactService = contactService;
        this.rateLimitingService = rateLimitingService;
    }

    @PostMapping
    public ResponseEntity<?> submitContact(@RequestBody ContactRequestDTO dto, HttpServletRequest request) {

        // 1. Obtener la IP real (Manejo de Proxies)
        String clientIp = getClientIp(request);

        // 2. Aplicar Rate Limiting
        Bucket bucket = rateLimitingService.resolveBucket(clientIp);
        if (!bucket.tryConsume(1)) {
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                    .body("Has superado el límite de mensajes. Por favor, intenta de nuevo más tarde.");
        }

        // 3. Sanitización básica
        if (dto.getEmail() == null || dto.getMessage() == null || dto.getName() == null) {
            return ResponseEntity.badRequest().body("Faltan campos obligatorios");
        }

        // 4. Procesamiento
        contactService.processContactRequest(dto);

        return ResponseEntity.ok("Mensaje recibido correctamente. Te contactaremos pronto.");
    }

    // Método utilitario para leer la IP correctamente si usamos Docker o Nginx
    private String getClientIp(HttpServletRequest request) {
        String ipAddress = request.getHeader("X-Forwarded-For");
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getRemoteAddr();
        }
        // Si pasa por múltiples proxies, tomamos la primera IP
        if (ipAddress != null && ipAddress.contains(",")) {
            ipAddress = ipAddress.split(",")[0];
        }
        return ipAddress;
    }
}
