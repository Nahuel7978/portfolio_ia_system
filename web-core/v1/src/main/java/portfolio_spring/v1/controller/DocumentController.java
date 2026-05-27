package portfolio_spring.v1.controller;

import org.springframework.http.HttpHeaders;
import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import portfolio_spring.v1.dto.DocumentResponseDTO;
import portfolio_spring.v1.model.Document;
import portfolio_spring.v1.service.DocumentService;

@RestController
@RequestMapping("/api/v1/admin/knowledge-entries")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @PostMapping(value = "/{id}/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> uploadDocument(
            @PathVariable("id") Integer entryId,
            @RequestParam("file") MultipartFile file,
            @RequestParam("docType") String docType,
            @RequestParam("technicalDepth") Integer technicalDepth,
            @RequestParam("language") String language,
            @RequestParam("importance") Integer importance) {
        try {
            documentService.uploadDocument(entryId, file, docType, technicalDepth, language, importance);
            // Evitamos devolver la entidad completa para no retornar el BYTEA.
            // En un caso real, aquí usaríamos el DocumentResponseDTO.
            return ResponseEntity.status(HttpStatus.CREATED).body("Documento cargado exitosamente en estado PENDING.");

        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.UNSUPPORTED_MEDIA_TYPE).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error procesando el archivo.");
        }
    }

    @GetMapping("/{id}/documents")
    public ResponseEntity<List<DocumentResponseDTO>> getDocumentsByEntry(@PathVariable("id") Integer entryId) {
        List<DocumentResponseDTO> documents = documentService.getDocumentsByEntryId(entryId);
        return ResponseEntity.ok(documents);
    }

    @DeleteMapping("/documents/{documentId}")
    public ResponseEntity<?> deleteDocument(@PathVariable("documentId") Integer documentId) {
        try {
            documentService.deleteDocument(documentId);
            return ResponseEntity.noContent().build(); // Retorna 204 No Content
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }

    // Endpoint 2: Descargar el archivo físico
    @GetMapping("/documents/{documentId}/download")
    public ResponseEntity<byte[]> downloadDocument(@PathVariable("documentId") Integer documentId) {
        Document document = documentService.getDocumentForDownload(documentId);

        return ResponseEntity.ok()
                // Indica al navegador que es un archivo adjunto y sugiere el nombre original
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + document.getDocumentName() + "\"")
                // Inyecta el MIME type real guardado en la base de datos (ej. application/pdf)
                .contentType(MediaType.parseMediaType(document.getMimeType()))
                .body(document.getFileData());
    }
}
