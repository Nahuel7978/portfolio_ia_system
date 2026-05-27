package portfolio_spring.v1.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import portfolio_spring.v1.dto.KnowledgeEntryDTO;
import portfolio_spring.v1.dto.TechnologyRoleDTO;
import portfolio_spring.v1.mapper.KnowledgeEntryMapper;
import portfolio_spring.v1.model.KnowledgeEntry;
import portfolio_spring.v1.model.Technology;
import portfolio_spring.v1.repository.DocumentRepository;
import portfolio_spring.v1.repository.KnowledgeEntryRepository;
import portfolio_spring.v1.repository.TechnologyRepository;
import portfolio_spring.v1.dto.PublicEntryDetailDTO;
import portfolio_spring.v1.model.Document;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class KnowledgeEntryService {

    private final KnowledgeEntryRepository entryRepository;
    private final TechnologyRepository technologyRepository;
    private final DocumentRepository documentRepository;

    private final DocumentService documentService;

    private final KnowledgeEntryMapper mapper;


    private static final List<String> VALID_AREAS = Arrays.asList(
            "AI", "ML", "Robotics", "NLP", "Web", "Programming", "Computer Vision", "Data Analytics", "Education", "Activity", "Languages", "Blog"
    );
    private static final List<String> VALID_STATUS = Arrays.asList("active", "completed");
    private static final List<String> VALID_ROLES = Arrays.asList("primary", "secondary");

    public KnowledgeEntryService(KnowledgeEntryRepository entryRepository, TechnologyRepository technologyRepository, KnowledgeEntryMapper mapper, DocumentService documentService, DocumentRepository documentRepository){
        this.entryRepository = entryRepository;
        this.documentService = documentService;
        this.mapper = mapper;
        this.technologyRepository = technologyRepository;
        this.documentRepository = documentRepository;
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
    public KnowledgeEntryDTO createEntry(KnowledgeEntryDTO dto, MultipartFile image) throws IOException {
        // 1. Mapeo normal del DTO a la Entidad (tu lógica actual)
        KnowledgeEntry entry = mapper.toEntity(dto);

        // 2. Procesamiento de la imagen (Opcional)
        if (image != null && !image.isEmpty()) {
            String contentType = image.getContentType();

            // Validación básica de seguridad
            if (contentType == null || !contentType.startsWith("image/")) {
                throw new IllegalArgumentException("El archivo adjunto debe ser una imagen válida.");
            }

            entry.setImageData(image.getBytes());
            entry.setImageMimeType(contentType);
        }

        // 3. Guardado en base de datos
        KnowledgeEntry savedEntry = entryRepository.save(entry);

        // 4. Retornamos el DTO limpio (sin la imagen, como queríamos)
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

    @Transactional(readOnly = true)
    public List<KnowledgeEntryDTO> getPublicProjects() {
        // Excluimos Activity y Blog
        List<KnowledgeEntry> projects = entryRepository.findByAreaNotIn(List.of("Activity", "Blog"));
        return projects.stream()
                .map(mapper::toDTO)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<KnowledgeEntryDTO> getPublicBlogs() {
        // Incluimos solo Activity y Blog
        List<KnowledgeEntry> blogs = entryRepository.findByAreaIn(List.of("Activity", "Blog"));
        return blogs.stream()
                .map(mapper::toDTO)
                .toList();
    }

    @Transactional(readOnly = true)
    public PublicEntryDetailDTO getPublicEntryById(Integer id) {
        KnowledgeEntry entry = entryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Proyecto no encontrado"));

        PublicEntryDetailDTO detailDTO = new PublicEntryDetailDTO();
        detailDTO.setEntry(mapper.toDTO(entry));

        // Buscar si tiene un documento summary asociado
        Optional<Document> summaryOpt = documentRepository.findFirstByEntryIdAndDocType(id, "summary");

        if (summaryOpt.isPresent()) {
            Document summary = summaryOpt.get();
            detailDTO.setSummaryDocumentId(summary.getId());
            // Transformar el BYTEA a String UTF-8 para que Angular lo consuma como texto
            if (summary.getFileData() != null) {
                String markdownText = new String(summary.getFileData(), StandardCharsets.UTF_8);
                detailDTO.setSummaryMarkdown(markdownText);
            }
        }

        return detailDTO;
    }

    @Transactional
    public void deleteEntry(Integer id) {
        if (!entryRepository.existsById(id)) {
            throw new RuntimeException("Entrada no encontrada");
        }

        // 1. Limpiamos primero los documentos físicos dependientes
        documentService.deleteDocumentsByEntryId(id);

        // 2. Luego eliminamos la entrada (JPA ya se encarga de la tabla intermedia de tecnologías por el orphanRemoval=true)
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

	public KnowledgeEntry getEntryEntityById(Integer id) {
		// TODO Auto-generated method stub
		KnowledgeEntry entry = entryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Proyecto no encontrado"));
		return entry;
	}

	@Transactional
    public void updateCoverImage(Integer id, MultipartFile newImage) throws IOException {
        KnowledgeEntry entry = entryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Proyecto no encontrado con ID: " + id));

        if (newImage == null || newImage.isEmpty()) {
            throw new IllegalArgumentException("El archivo de imagen no puede estar vacío.");
        }

        String contentType = newImage.getContentType();
        if (contentType == null || !contentType.startsWith("image/")) {
            throw new IllegalArgumentException("El archivo adjunto debe ser una imagen válida.");
        }

        //Sobrescribimos los datos (esto "elimina" la imagen anterior en la BD)
        entry.setImageData(newImage.getBytes());
        entry.setImageMimeType(contentType);

        //Guardamos los cambios
        entryRepository.save(entry);
    }

    @Transactional
    public void deleteCoverImage(Integer id) {
        KnowledgeEntry entry = entryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Proyecto no encontrado con ID: " + id));

        entry.setImageData(null);
        entry.setImageMimeType(null);
        entryRepository.save(entry);
    }
}
