package portfolio_spring.v1.dto;

import java.util.ArrayList;
import java.util.List;

public class KnowledgeEntryDTO {
    private Integer id;
    private String name;
    private String area;
    private String areaSecondary;
    private String status;
    private List<TechnologyRoleDTO> technologies = new ArrayList<>();

    // Constructores, Getters y Setters
    public KnowledgeEntryDTO() {}

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getArea() { return area; }
    public void setArea(String area) { this.area = area; }
    public String getAreaSecondary() { return areaSecondary; }
    public void setAreaSecondary(String areaSecondary) { this.areaSecondary = areaSecondary; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public List<TechnologyRoleDTO> getTechnologies() { return technologies; }
    public void setTechnologies(List<TechnologyRoleDTO> technologies) { this.technologies = technologies; }
}
