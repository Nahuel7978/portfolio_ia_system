package portfolio_spring.v1.mapper;

import org.springframework.stereotype.Component;
import portfolio_spring.v1.dto.KnowledgeEntryDTO;
import portfolio_spring.v1.dto.TechnologyRoleDTO;
import portfolio_spring.v1.model.KnowledgeEntry;
import portfolio_spring.v1.model.KnowledgeEntryTechnology;
import portfolio_spring.v1.model.Technology;
import portfolio_spring.v1.service.TechnologyService;

import java.util.ArrayList;
import java.util.Iterator;
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

        dto.setHasCoverImage(entry.getImageData() != null);
        return dto;
    }

	public static KnowledgeEntry toEntity(KnowledgeEntryDTO dto) {
		// TODO Auto-generated method stub
		if (dto == null) {
	        return null;
	    }

		KnowledgeEntry ke = new KnowledgeEntry();
		if (dto.getId() != null) {
	        ke.setId(dto.getId());
	    }
		ke.setName(dto.getName());
		ke.setArea(dto.getArea());
		ke.setAreaSecondary(dto.getAreaSecondary());
		ke.setStatus(dto.getStatus());

		List<TechnologyRoleDTO> listTec = dto.getTechnologies();
	    if (listTec != null && !listTec.isEmpty()) {
			List<KnowledgeEntryTechnology> tecnologies = new ArrayList<KnowledgeEntryTechnology>();
			for (TechnologyRoleDTO tecDTO : listTec) {
				KnowledgeEntryTechnology ket = new KnowledgeEntryTechnology();
				Technology tech = new Technology();

				ket.setRole(tecDTO.getRole());
				tech.setId(tecDTO.getTechnologyId());
				ket.setTechnology(tech);

				ket.setEntry(ke);//Vinculamos la relación bidireccional

				tecnologies.add(ket);
			}
			ke.setEntryTechnologies(tecnologies);
		}

		return ke;
	}
}
