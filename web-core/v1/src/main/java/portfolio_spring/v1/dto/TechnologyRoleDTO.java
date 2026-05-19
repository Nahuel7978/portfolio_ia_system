package portfolio_spring.v1.dto;

public class TechnologyRoleDTO {
    private Integer technologyId;
    private String name; // Solo de lectura (para las respuestas)
    private String role; // 'primary' o 'secondary'

    public TechnologyRoleDTO() {}

    public TechnologyRoleDTO(Integer technologyId, String name, String role) {
        this.technologyId = technologyId;
        this.name = name;
        this.role = role;
    }

    // Getters y Setters
    public Integer getTechnologyId() { return technologyId; }
    public void setTechnologyId(Integer technologyId) { this.technologyId = technologyId; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
}
