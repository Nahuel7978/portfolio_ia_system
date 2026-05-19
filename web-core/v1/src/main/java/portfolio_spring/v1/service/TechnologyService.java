package portfolio_spring.v1.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import portfolio_spring.v1.dto.TechnologyDTO;
import portfolio_spring.v1.model.Technology;
import portfolio_spring.v1.repository.TechnologyRepository;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class TechnologyService {

    private final TechnologyRepository technologyRepository;

    // Lista de categorías permitidas en tu base de datos PostgreSQL
    private static final List<String> VALID_CATEGORIES = Arrays.asList(
        "language", "framework", "library", "tool", "algorithm", "infrastructure", "platform"
    );

    public TechnologyService(TechnologyRepository technologyRepository) {
        this.technologyRepository = technologyRepository;
    }

    @Transactional(readOnly = true)
    public List<TechnologyDTO> getAllTechnologies() {
        return technologyRepository.findAll().stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public TechnologyDTO getTechnologyById(Integer id) {
        Technology tech = technologyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Tecnología no encontrada"));
        return convertToDTO(tech);
    }

    @Transactional
    public TechnologyDTO createTechnology(TechnologyDTO dto) {
        validateCategory(dto.getCategory());
        if (technologyRepository.existsByName(dto.getName())) {
            throw new RuntimeException("La tecnología ya existe: " + dto.getName());
        }

        Technology tech = new Technology();
        tech.setName(dto.getName());
        tech.setCategory(dto.getCategory());

        Technology saved = technologyRepository.save(tech);
        return convertToDTO(saved);
    }

    @Transactional
    public TechnologyDTO updateTechnology(Integer id, TechnologyDTO dto) {
        validateCategory(dto.getCategory());

        Technology tech = technologyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Tecnología no encontrada"));

        tech.setName(dto.getName());
        tech.setCategory(dto.getCategory());

        Technology updated = technologyRepository.save(tech);
        return convertToDTO(updated);
    }

    @Transactional
    public void deleteTechnology(Integer id) {
        if (!technologyRepository.existsById(id)) {
            throw new RuntimeException("Tecnología no encontrada");
        }
        technologyRepository.deleteById(id);
    }

    // --- Métodos Utilitarios ---
    private void validateCategory(String category) {
        if (!VALID_CATEGORIES.contains(category)) {
            throw new IllegalArgumentException("Categoría inválida. Debe ser una de: " + VALID_CATEGORIES);
        }
    }

    private TechnologyDTO convertToDTO(Technology tech) {
        return new TechnologyDTO(tech.getId(), tech.getName(), tech.getCategory());
    }
}
