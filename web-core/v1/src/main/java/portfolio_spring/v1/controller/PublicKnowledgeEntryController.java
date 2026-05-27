package portfolio_spring.v1.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;

import portfolio_spring.v1.dto.KnowledgeEntryDTO;
import portfolio_spring.v1.dto.PublicEntryDetailDTO;
import portfolio_spring.v1.model.KnowledgeEntry;
import portfolio_spring.v1.service.KnowledgeEntryService;

import java.util.List;

@RestController
@RequestMapping("/api/v1/public/knowledge-entries")
public class PublicKnowledgeEntryController {

    private final KnowledgeEntryService knowledgeEntryService;

    public PublicKnowledgeEntryController(KnowledgeEntryService knowledgeEntryService) {
        this.knowledgeEntryService = knowledgeEntryService;
    }

    @GetMapping("/projects")
    public ResponseEntity<List<KnowledgeEntryDTO>> getProjects() {
        return ResponseEntity.ok(knowledgeEntryService.getPublicProjects());
    }

    @GetMapping("/blogs")
    public ResponseEntity<List<KnowledgeEntryDTO>> getBlogs() {
        return ResponseEntity.ok(knowledgeEntryService.getPublicBlogs());
    }

    @GetMapping("/{id}/image")
    public ResponseEntity<byte[]> getProjectCoverImage(@PathVariable("id") Integer id) {
        // Aquí puedes crear un método en tu servicio que haga un SELECT solo de la imagen
        KnowledgeEntry entry= knowledgeEntryService.getEntryEntityById(id);
        byte[] image = entry.getImageData();

        if (image == null) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok()
                .header(HttpHeaders.CACHE_CONTROL, "max-age=3600") // Cacheo en el navegador
                .contentType(MediaType.parseMediaType(entry.getImageMimeType()))
                .body(image);
    }

    @GetMapping("/{id}")
    public ResponseEntity<PublicEntryDetailDTO> getEntryDetail(@PathVariable("id") Integer id) {
        try {
            PublicEntryDetailDTO detail = knowledgeEntryService.getPublicEntryById(id);
            return ResponseEntity.ok(detail);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
}
