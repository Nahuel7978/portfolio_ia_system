package portfolio_spring.v1.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import portfolio_spring.v1.dto.KnowledgeEntryDTO;
import portfolio_spring.v1.dto.TechnologyRoleDTO;
import portfolio_spring.v1.mapper.KnowledgeEntryMapper;
import portfolio_spring.v1.model.KnowledgeEntry;
import portfolio_spring.v1.model.Technology;
import portfolio_spring.v1.repository.KnowledgeEntryRepository;
import portfolio_spring.v1.repository.TechnologyRepository;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class KnowledgeEntryService {

    private final KnowledgeEntryRepository entryRepository;
    private final TechnologyRepository technologyRepository;
    private final KnowledgeEntryMapper mapper;

    private static final List<String> VALID_AREAS = Arrays.asList(
            "AI", "ML", "Robotics", "NLP", "Web", "Programming", "Computer Vision", "Data Analytics", "Education", "Activity", "Languages"
    );
    private static final List<String> VALID_STATUS = Arrays.asList("active", "completed");
    private static final List<String> VALID_ROLES = Arrays.asList("primary", "secondary");

    public KnowledgeEntryService(KnowledgeEntryRepository entryRepository, TechnologyRepository technologyRepository, KnowledgeEntryMapper mapper) {
        this.entryRepository = entryRepository;
        this.technologyRepository = technologyRepository;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public List<KnowledgeEntryDTO> getAllEntries() {
        return entryRepository.findAll().stream()
                .map(mapper::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public KnowledgeEntryDTO getEntryById(Integer id) {
        KnowledgeEntry entry = entryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Entrada no encontrada"));
        return mapper.toDTO(entry);
    }

    @Transactional
    public KnowledgeEntryDTO createEntry(KnowledgeEntryDTO dto) {
        validateEnums(dto);
        KnowledgeEntry entry = new KnowledgeEntry();
        updateEntityBasicFields(entry, dto);
        assignTechnologiesToEntry(entry, dto.getTechnologies());

        KnowledgeEntry savedEntry = entryRepository.save(entry);
        return mapper.toDTO(savedEntry);
    }

    @Transactional
    public KnowledgeEntryDTO updateEntry(Integer id, KnowledgeEntryDTO dto) {
        validateEnums(dto);
        KnowledgeEntry entry = entryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Entrada no encontrada"));

        updateEntityBasicFields(entry, dto);

        // Limpiar la lista actual dispara el orphanRemoval=true en JPA
        entry.getEntryTechnologies().clear();

        entryRepository.flush();

        assignTechnologiesToEntry(entry, dto.getTechnologies());

        KnowledgeEntry updatedEntry = entryRepository.save(entry);
        return mapper.toDTO(updatedEntry);
    }

    @Transactional
    public void deleteEntry(Integer id) {
        if (!entryRepository.existsById(id)) {
            throw new RuntimeException("Entrada no encontrada");
        }
        entryRepository.deleteById(id);
    }

    // --- Métodos Utilitarios Internos ---
    private void validateEnums(KnowledgeEntryDTO dto) {
        if (!VALID_AREAS.contains(dto.getArea())) throw new IllegalArgumentException("Área primaria inválida.");
        if (dto.getAreaSecondary() != null && !VALID_AREAS.contains(dto.getAreaSecondary())) {
            throw new IllegalArgumentException("Área secundaria inválida.");
        }
        if (!VALID_STATUS.contains(dto.getStatus())) throw new IllegalArgumentException("Status inválido.");
    }

    private void updateEntityBasicFields(KnowledgeEntry entry, KnowledgeEntryDTO dto) {
        entry.setName(dto.getName());
        entry.setArea(dto.getArea());
        entry.setAreaSecondary(dto.getAreaSecondary());
        entry.setStatus(dto.getStatus());
    }

    private void assignTechnologiesToEntry(KnowledgeEntry entry, List<TechnologyRoleDTO> techRoles) {
        if (techRoles != null) {
            for (TechnologyRoleDTO techRole : techRoles) {
                if (!VALID_ROLES.contains(techRole.getRole())) {
                    throw new IllegalArgumentException("Rol inválido: " + techRole.getRole());
                }
                Technology tech = technologyRepository.findById(techRole.getTechnologyId())
                        .orElseThrow(() -> new RuntimeException("Tecnología no encontrada: ID " + techRole.getTechnologyId()));
                entry.addTechnology(tech, techRole.getRole());
            }
        }
    }
}
