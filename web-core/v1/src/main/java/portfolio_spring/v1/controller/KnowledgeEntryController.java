package portfolio_spring.v1.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import portfolio_spring.v1.dto.KnowledgeEntryDTO;
import portfolio_spring.v1.service.KnowledgeEntryService;

import org.springframework.http.MediaType;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.util.List;

@RestController
@RequestMapping("/api/v1/admin/knowledge-entries")
public class KnowledgeEntryController {

    private final KnowledgeEntryService entryService;

    public KnowledgeEntryController(KnowledgeEntryService entryService) {
        this.entryService = entryService;
    }

    @GetMapping
    public ResponseEntity<List<KnowledgeEntryDTO>> getAll() {
        return ResponseEntity.ok(entryService.getAllEntries());
    }

    @GetMapping("/{id}")
    public ResponseEntity<KnowledgeEntryDTO> getById(@PathVariable Integer id) {
        try {
            return ResponseEntity.ok(entryService.getEntryById(id));
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> createEntry(
            @RequestPart("data") KnowledgeEntryDTO data,
            @RequestPart(value = "image", required = false) MultipartFile image) {
        try {
            KnowledgeEntryDTO createdEntry = entryService.createEntry(data, image);
            return ResponseEntity.status(HttpStatus.CREATED).body(createdEntry);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.UNSUPPORTED_MEDIA_TYPE).body(e.getMessage());
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error procesando la imagen");
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> update(@PathVariable Integer id, @RequestBody KnowledgeEntryDTO dto) {
        try {
            KnowledgeEntryDTO updated = entryService.updateEntry(id, dto);
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }

    @PutMapping(value = "/{id}/image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> updateCoverImage(
            @PathVariable("id") Integer id,
            @RequestPart("image") MultipartFile image) {
        try {
        	entryService.updateCoverImage(id, image);
            return ResponseEntity.ok("Imagen actualizada correctamente.");
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.UNSUPPORTED_MEDIA_TYPE).body(e.getMessage());
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error procesando la nueva imagen.");
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }

    @DeleteMapping("/{id}/image")
    public ResponseEntity<?> deleteCoverImage(@PathVariable("id") Integer id) {
        try {
        	entryService.deleteCoverImage(id);
            return ResponseEntity.noContent().build(); // Retorna 204 No Content
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }


    @DeleteMapping("/{id}")
    public ResponseEntity<?> delete(@PathVariable Integer id) {
        try {
            entryService.deleteEntry(id);
            return ResponseEntity.noContent().build();
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }
}
