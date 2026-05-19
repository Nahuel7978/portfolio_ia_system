package portfolio_spring.v1.model;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "knowledge_entries")
public class KnowledgeEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private String area;

    @Column(name = "area_secondary")
    private String areaSecondary;

    @Column(nullable = false)
    private String status;

    @OneToMany(mappedBy = "knowledgeEntry", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<KnowledgeEntryTechnology> entryTechnologies = new ArrayList<>();

    // Método utilitario para mantener sincronización bidireccional (Buenas Prácticas JPA)
    public void addTechnology(Technology technology, String role) {
        KnowledgeEntryTechnology ket = new KnowledgeEntryTechnology();
        ket.setKnowledgeEntry(this);
        ket.setTechnology(technology);
        ket.setRole(role);
        entryTechnologies.add(ket);
    }

    // Getters y Setters
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
    public List<KnowledgeEntryTechnology> getEntryTechnologies() { return entryTechnologies; }
    public void setEntryTechnologies(List<KnowledgeEntryTechnology> entryTechnologies) { this.entryTechnologies = entryTechnologies; }
}
