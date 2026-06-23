package portfolio_spring.v1.scheduler;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import portfolio_spring.v1.model.Document;
import portfolio_spring.v1.model.KnowledgeEntry;
import portfolio_spring.v1.repository.DocumentRepository;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
public class DocumentSyncScheduler {

    private static final Logger logger = LoggerFactory.getLogger(DocumentSyncScheduler.class);
    
    private final DocumentRepository documentRepository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${FASTAPI_URL}")
    private String fastApiUrl;

    @Value("${X_INTERNAL_SECRET}")
    private String internalSecret; 

    public DocumentSyncScheduler(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
        this.restTemplate = new RestTemplate(); // Cliente HTTP manual
        this.objectMapper = new ObjectMapper(); // Serializador JSON manual
    }

    @Scheduled(fixedDelay = 300000)
    @Transactional // Mantiene la sesión de Hibernate abierta para el Lazy Loading
    public void processPendingDocuments() {
        logger.info("Iniciando escaneo de Consistencia Eventual para documentos...");

        List<Document> pendingDocs = documentRepository.findBySyncStatusIn(Arrays.asList("PENDING", "FAILED"));

        if (pendingDocs.isEmpty()) {
            logger.info("No hay documentos pendientes de sincronización.");
            return;
        }

        for (Document doc : pendingDocs) {
            executeFastApiSync(doc);
        }

        logger.info("Escaneo finalizado.");
    }

    private void executeFastApiSync(Document doc) {
        logger.info("Enviando documento ID: {} (Tipo: {}) a FastAPI para vectorización...", doc.getId(), doc.getDocType());

        try {
            KnowledgeEntry entry = doc.getEntry();

            // 1. Construir la Metadata (Mapeo a JSON)
            Map<String, Object> metadata = new HashMap<>();
            metadata.put("document_id", doc.getId());
            metadata.put("entry_id", entry.getId());
            metadata.put("entry_name", entry.getName());
            metadata.put("doc_type", doc.getDocType());
            metadata.put("area", entry.getArea());
            metadata.put("area_secondary", entry.getAreaSecondary());
            metadata.put("document_name", doc.getDocumentName());
            metadata.put("technical_depth", doc.getTechnicalDepth());

            // Extraer tecnologías asociadas a la entry de forma segura (asumiendo relación ManyToMany u OneToMany)
            if (entry.getEntryTechnologies() != null) {
                String techs = entry.getEntryTechnologies().stream()
                        // Ajusta 'getTechnology().getName()' según cómo esté estructurada tu entidad intermedia
                        .map(t -> t.getTechnology().getName()) 
                        .collect(Collectors.joining(", "));
                metadata.put("technologies", techs);
            }

            String metadataJson = objectMapper.writeValueAsString(metadata);

            // 2. Construir el Body (Multipart)
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new NamedByteArrayResource(doc.getFileData(), doc.getDocumentName()));
            body.add("metadata", metadataJson);

            // 3. Configurar Headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            headers.set("X-Internal-Secret", internalSecret);

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            // 4. Ejecutar Petición
            ResponseEntity<String> response = restTemplate.postForEntity(fastApiUrl, requestEntity, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                logger.info("✅ Documento {} vectorizado con éxito.", doc.getId());
                doc.setSyncStatus("SYNCED");
            } else {
                logger.warn("⚠️ Falló la vectorización del documento {}. Código: {}", doc.getId(), response.getStatusCode());
                doc.setSyncStatus("FAILED");
            }

        } catch (Exception e) {
            logger.error("❌ Error de red o serialización al enviar el documento {}: {}", doc.getId(), e.getMessage());
            doc.setSyncStatus("FAILED");
        }
        
        // Guardar el estado actualizado en la DB
        documentRepository.save(doc);
    }

    // --- Clase Utilitaria para forzar el envío del nombre del archivo ---
    private static class NamedByteArrayResource extends ByteArrayResource {
        private final String filename;

        public NamedByteArrayResource(byte[] byteArray, String filename) {
            super(byteArray);
            this.filename = filename;
        }

        @Override
        public String getFilename() {
            return this.filename;
        }
    }
}
