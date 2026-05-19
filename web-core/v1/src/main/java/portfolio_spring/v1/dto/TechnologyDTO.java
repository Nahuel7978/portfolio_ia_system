package portfolio_spring.v1.dto;

public class TechnologyDTO {

    private Integer id;
    private String name;
    private String category;

    // Constructores
    public TechnologyDTO() {}

    public TechnologyDTO(Integer id, String name, String category) {
        this.id = id;
        this.name = name;
        this.category = category;
    }

    // Getters y Setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
}
