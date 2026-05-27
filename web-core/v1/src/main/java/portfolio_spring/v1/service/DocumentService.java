package portfolio_spring.v1.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import portfolio_spring.v1.dto.DocumentResponseDTO;
import portfolio_spring.v1.model.Document;
import portfolio_spring.v1.model.KnowledgeEntry;
import portfolio_spring.v1.repository.DocumentRepository;
import portfolio_spring.v1.repository.KnowledgeEntryRepository;

import java.io.IOException;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class DocumentService {

    private final DocumentRepository documentRepository;
    private final KnowledgeEntryRepository entryRepository;

    public DocumentService(DocumentRepository documentRepository, KnowledgeEntryRepository entryRepository) {
        this.documentRepository = documentRepository;
        this.entryRepository = entryRepository;
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
    }
}
