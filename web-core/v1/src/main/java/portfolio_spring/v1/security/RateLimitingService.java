package portfolio_spring.v1.security;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class RateLimitingService {

    // Caché en memoria para guardar el "cubo" de peticiones de cada IP
    private final Map<String, Bucket> cache = new ConcurrentHashMap<>();

    public Bucket resolveBucket(String ip) {
        return cache.computeIfAbsent(ip, this::newBucket);
    }

    private Bucket newBucket(String ip) {
        // Regla: Máximo 2 peticiones. Se recargan 2 peticiones cada 1 hora.
        Refill refill = Refill.greedy(2, Duration.ofHours(1));
        Bandwidth limit = Bandwidth.classic(2, refill);
        return Bucket.builder().addLimit(limit).build();
    }
}
