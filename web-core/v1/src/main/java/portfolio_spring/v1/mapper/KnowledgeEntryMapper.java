package portfolio_spring.v1.mapper;

import org.springframework.stereotype.Component;
import portfolio_spring.v1.dto.KnowledgeEntryDTO;
import portfolio_spring.v1.dto.TechnologyRoleDTO;
import portfolio_spring.v1.model.KnowledgeEntry;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class KnowledgeEntryMapper {

    public KnowledgeEntryDTO toDTO(KnowledgeEntry entry) {
        KnowledgeEntryDTO dto = new KnowledgeEntryDTO();
        dto.setId(entry.getId());
        dto.setName(entry.getName());
        dto.setArea(entry.getArea());
        dto.setAreaSecondary(entry.getAreaSecondary());
        dto.setStatus(entry.getStatus());

        if (entry.getEntryTechnologies() != null) {
            List<TechnologyRoleDTO> techDTOs = entry.getEntryTechnologies().stream()
                    .map(ket -> new TechnologyRoleDTO(
                            ket.getTechnology().getId(),
                            ket.getTechnology().getName(),
                            ket.getRole()
                    )).collect(Collectors.toList());
            dto.setTechnologies(techDTOs);
        }
        return dto;
    }
}
