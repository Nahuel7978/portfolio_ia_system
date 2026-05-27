package portfolio_spring.v1.scheduler;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import portfolio_spring.v1.model.Document;
import portfolio_spring.v1.repository.DocumentRepository;

import java.util.Arrays;
import java.util.List;

@Component
public class DocumentSyncScheduler {

    private static final Logger logger = LoggerFactory.getLogger(DocumentSyncScheduler.class);
    private final DocumentRepository documentRepository;

    public DocumentSyncScheduler(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
    }

    // Se ejecuta cada 5 minutos (300000 ms) después de que termine la ejecución anterior
    @Scheduled(fixedDelay = 300000)
    @Transactional(readOnly = true) // readOnly porque solo estamos consultando y simulando
    public void processPendingDocuments() {
        logger.info("Iniciando escaneo de Consistencia Eventual para documentos...");

        // 1. Recuperar documentos pendientes o fallidos
        List<Document> pendingDocs = documentRepository.findBySyncStatusIn(Arrays.asList("PENDING", "FAILED"));

        if (pendingDocs.isEmpty()) {
            logger.info("No hay documentos pendientes de sincronización.");
            return;
        }

        // 2. Procesar cada documento (Desacoplado)
        for (Document doc : pendingDocs) {
            simulateFastApiSync(doc);
        }

        logger.info("Escaneo finalizado.");
    }

    private void simulateFastApiSync(Document doc) {
        // En el Sprint 5, aquí inyectaremos un cliente HTTP para enviar el payload a FastAPI.
        // Por ahora, cumplimos el entregable del Sprint 2 mockeando la acción.
        logger.info("[MOCK] Enviando documento ID: {} (Tipo: {}) a FastAPI para vectorización...",
                    doc.getId(), doc.getDocType());

        // Simulación de respuesta exitosa de FastAPI:
        // doc.setSyncStatus("SYNCED");
        // documentRepository.save(doc);
    }
}
