package portfolio_spring.v1.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import portfolio_spring.v1.dto.KnowledgeEntryDTO;
import portfolio_spring.v1.service.KnowledgeEntryService;

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

    @PostMapping
    public ResponseEntity<?> create(@RequestBody KnowledgeEntryDTO dto) {
        try {
            KnowledgeEntryDTO created = entryService.createEntry(dto);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(e.getMessage());
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
