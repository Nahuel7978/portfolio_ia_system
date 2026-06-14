import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AdminEntryService } from '../../../core/services/admin-entry.service';
import { TechnologyService } from '../../../core/services/technology.service';
import { Technology } from '../../../core/models/technology.interface';
import { ActivatedRoute, Router } from '@angular/router';
import { concatMap, from, toArray } from 'rxjs';

interface DocumentQueueItem {
  file: File;
  docType: string;
  technicalDepth: number;
  language: string;
  importance: number;
}

@Component({
  selector: 'app-entry-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './entries-form.html'
})
export class EntryFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private entryService = inject(AdminEntryService);
  private techService = inject(TechnologyService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  entryType: 'project' | 'blog' = 'project';
  isSubmitting = false;

  // Listas Dinámicas
  primaryAreas: string[] = [];
  secondaryAreas: string[] = [];
  technologies: Technology[] = [];
  
  // Estado del Formulario
  entryForm: FormGroup;
  selectedTechs: { technologyId: number, role: string, name: string }[] = [];
  coverImage: File | null = null;
  
  // Estado de Documentos
  summaryDoc: DocumentQueueItem | null = null;
  additionalDocs: DocumentQueueItem[] = [];

  constructor() {
    this.entryForm = this.fb.group({
      name: ['', Validators.required],
      area: ['', Validators.required],
      areaSecondary: [''],
      status: ['active', Validators.required]
    });
  }

  ngOnInit() {
    this.techService.getTechnologies().subscribe(data => this.technologies = data);
    
    this.route.queryParams.subscribe(params => {
      this.entryType = params['type'] === 'blogs' ? 'blog' : 'project';
      this.setupAreas();
    });
  }

  private setupAreas() {
    const blogAreas = ['Education', 'Activity', 'Languages', 'Blog'];
    const projectAreas = ['AI', 'ML', 'Robotics', 'NLP', 'Web', 'Programming', 'Computer Vision', 'Data Analytics'];

    if (this.entryType === 'blog') {
      this.primaryAreas = ['Blog', 'Activity', 'Education', 'Languages'];
      this.secondaryAreas = blogAreas;
    } else {
      this.primaryAreas = projectAreas;
      this.secondaryAreas = projectAreas;
    }
    
    // Resetear valores si cambian las listas
    this.entryForm.patchValue({ area: '', areaSecondary: '' });
  }

  // --- MÉTODOS DE TECNOLOGÍAS ---
  addTechnology(techId: string, role: string) {
    if (!techId || !role) return;
    const tech = this.technologies.find(t => t.id === Number(techId));
    if (tech && !this.selectedTechs.find(s => s.technologyId === tech.id)) {
      this.selectedTechs.push({ technologyId: tech.id!, role, name: tech.name });
    }
  }

  removeTechnology(index: number) {
    this.selectedTechs.splice(index, 1);
  }

  // --- MÉTODOS DE ARCHIVOS ---
  onCoverSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) this.coverImage = input.files[0];
  }

  onSummarySelected(event: Event, language: string, depth: string, importance: string) {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      const file = input.files[0];
      if (!file.name.toLowerCase().endsWith('.md')) {
        alert('El documento principal (Summary) debe ser obligatoriamente un archivo Markdown (.md).');
        input.value = ''; // Resetea el input visualmente
        this.summaryDoc = null; // Purga el estado
        return;
      }

      this.summaryDoc = {
        file: file,
        docType: 'summary',
        language,
        technicalDepth: Number(depth),
        importance: Number(importance)
      };
    }
  }

  addAdditionalDoc(fileInput: HTMLInputElement, type: string, lang: string, depth: string, imp: string) {
    if (fileInput.files?.length && type && lang && depth && imp) {
      this.additionalDocs.push({
        file: fileInput.files[0],
        docType: type,
        language: lang,
        technicalDepth: Number(depth),
        importance: Number(imp)
      });
      fileInput.value = ''; // Reset input
    }
  }

  removeAdditionalDoc(index: number) {
    this.additionalDocs.splice(index, 1);
  }

  // --- ORQUESTACIÓN DE SUBIDA ---
  onSubmit() {
    if (this.entryForm.invalid || !this.summaryDoc) {
      alert("El formulario es inválido o falta el documento Summary.");
      return;
    }

    this.isSubmitting = true;

    // 1. Preparar Payload del Entry
    const entryData = new FormData();
    const entryDTO = {
      name: this.entryForm.value.name,
      area: this.entryForm.value.area,
      areaSecondary: this.entryForm.value.areaSecondary || null,
      status: this.entryForm.value.status,
      technologies: this.selectedTechs.map(t => ({ technologyId: t.technologyId, role: t.role }))
    };

    entryData.append('data', new Blob([JSON.stringify(entryDTO)], { type: 'application/json' }));
    if (this.coverImage) entryData.append('image', this.coverImage);

    // 2. Ejecutar cadena de peticiones
    this.entryService.createEntry(entryData).pipe(
      concatMap((newEntry: any) => {
        // Unir Summary + Adicionales en un solo array para subirlos iterativamente
        const allDocs = [this.summaryDoc!, ...this.additionalDocs];
        
        // Convertir el array a un flujo observable secuencial
        return from(allDocs).pipe(
          concatMap(doc => {
            const docForm = new FormData();
            docForm.append('file', doc.file);
            docForm.append('docType', doc.docType);
            docForm.append('technicalDepth', doc.technicalDepth.toString());
            docForm.append('language', doc.language);
            docForm.append('importance', doc.importance.toString());
            
            return this.entryService.uploadDocument(newEntry.id, docForm);
          }),
          toArray() // Esperar a que terminen todos los documentos
        );
      })
    ).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/admin/knowledge-entries']);
      },
      error: (err) => {
        console.error(err);
        alert('Ocurrió un error en la subida. Verifica la consola.');
        this.isSubmitting = false;
      }
    });
  }
}
