package portfolio_spring.v1.service;



import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.MultiValueMap;
import org.springframework.web.multipart.MultipartFile;

import portfolio_spring.v1.dto.DocumentResponseDTO;
import portfolio_spring.v1.model.Document;
import portfolio_spring.v1.model.KnowledgeEntry;
import portfolio_spring.v1.repository.DocumentRepository;
import portfolio_spring.v1.repository.KnowledgeEntryRepository;

import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.util.List;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class DocumentService {
	
	private static final Logger logger = LoggerFactory.getLogger(DocumentService.class);

    private final DocumentRepository documentRepository;
    private final KnowledgeEntryRepository entryRepository;
    
    private final RestTemplate restTemplate;
    private final String fastApiUrl = "http://localhost:8001/CV_BOT_API/v1/internal/documents";
    private final String internalSecret ="INTERNAL_INTERNAL";

    public DocumentService(DocumentRepository documentRepository, KnowledgeEntryRepository entryRepository) {
        this.documentRepository = documentRepository;
        this.entryRepository = entryRepository;
        this.restTemplate = new RestTemplate();
    }

    @Transactional
    public Document uploadDocument(Integer entryId, MultipartFile file, String docType,
                                   Integer technicalDepth, String language, Integer importance) throws IOException {

        // 1. Validar que la entrada exista
        KnowledgeEntry entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new RuntimeException("Knowledge Entry no encontrado"));

        // 2. Validar archivo vacío
        if (file.isEmpty()) {
            throw new IllegalArgumentException("El archivo no puede estar vacío");
        }

        // 3. Validar MIME Types estrictos (.pdf o .md)
        String contentType = file.getContentType();
        String filename = file.getOriginalFilename();

        boolean isPdf = "application/pdf".equals(contentType);
        // Los archivos Markdown pueden venir con diferentes MIME types dependiendo del OS/Navegador
        boolean isMd = filename != null && filename.toLowerCase().endsWith(".md") &&
                       ("text/markdown".equals(contentType) || "application/octet-stream".equals(contentType));

        if (!isPdf && !isMd) {
            throw new IllegalArgumentException("Tipo de archivo no soportado. Solo se permiten .pdf y .md");
        }

        if ("summary".equals(docType)) {
            boolean summaryExists = documentRepository.existsByEntryIdAndDocType(entryId, "summary");
            if (summaryExists) {
                throw new IllegalArgumentException("Ya existe un documento de tipo 'summary' para este proyecto. Modifique el existente o elimínelo primero.");
            }
        }

        // 4. Ensamblar la entidad
        Document document = new Document();
        document.setEntry(entry);
        document.setDocumentName(filename);
        document.setFileData(file.getBytes());
        document.setMimeType(isPdf ? "application/pdf" : "text/markdown");
        document.setDocType(docType);
        document.setTechnicalDepth(technicalDepth);
        document.setLanguage(language);
        document.setImportance(importance);
        document.setSyncStatus("PENDING"); // Obligatorio por requerimiento

        // 5. Persistir
        return documentRepository.save(document);
    }

    @Transactional(readOnly = true)
    public List<DocumentResponseDTO> getDocumentsByEntryId(Integer entryId) {
        List<Document> documents = documentRepository.findByEntryId(entryId);

        // Mapeo manual estricto para asegurar que NO invocamos doc.getFileData()
        return documents.stream().map(doc -> {
            DocumentResponseDTO dto = new DocumentResponseDTO();
            dto.setId(doc.getId());
            dto.setEntryId(doc.getEntry().getId());
            dto.setDocumentName(doc.getDocumentName());
            dto.setDocType(doc.getDocType());
            dto.setMimeType(doc.getMimeType());
            dto.setTechnicalDepth(doc.getTechnicalDepth());
            dto.setLanguage(doc.getLanguage());
            dto.setImportance(doc.getImportance());
            dto.setSyncStatus(doc.getSyncStatus());
            return dto;
        }).collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public Document getDocumentForDownload(Integer documentId) {
        return documentRepository.findById(documentId)
                .orElseThrow(() -> new RuntimeException("Documento no encontrado con ID: " + documentId));
    }

    @Transactional
    public void deleteDocumentsByEntryId(Integer entryId) {
        // Ejecuta el query de borrado masivo
        documentRepository.deleteByEntryId(entryId);
    }

    @Transactional
    public void deleteDocument(Integer documentId) {
        if (!documentRepository.existsById(documentId)) {
            throw new RuntimeException("Documento no encontrado con ID: " + documentId);
        }
        documentRepository.deleteById(documentId);
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Internal-Secret", internalSecret);
        HttpEntity<Void> requestEntity = new HttpEntity<>(headers);
        String deleteUrl = fastApiUrl + "/" + documentId;
        try {
            logger.info("Enviando petición DELETE a FastAPI para purgar el documento ID: {}", documentId);
            
            ResponseEntity<String> response = restTemplate.exchange(
                    deleteUrl,
                    HttpMethod.DELETE,
                    requestEntity,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                logger.info("✅ Documento {} purgado de ChromaDB exitosamente.", documentId);
            } else {
                logger.warn("⚠️ FastAPI devolvió código {} al intentar borrar el documento {}", response.getStatusCode(), documentId);
            }

        } catch (Exception e) {
            logger.error("❌ Error de red al intentar eliminar el documento {} de ChromaDB: {}", documentId, e.getMessage());
            
            // ATENCIÓN - DECISIÓN DE DISEÑO:
            // Si comentas la siguiente línea, un fallo en FastAPI cancelará el borrado en PostgreSQL.
            // Si no la comentas, PostgreSQL borrará el archivo, pero ChromaDB mantendrá "basura" si la red falla.
            throw new RuntimeException("No se pudo sincronizar la eliminación con el motor de IA.", e);
        }
    }
}
