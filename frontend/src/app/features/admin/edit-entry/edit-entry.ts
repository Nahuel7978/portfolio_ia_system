import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AdminEntryService } from '../../../core/services/admin-entry.service';
import { TechnologyService } from '../../../core/services/technology.service';
import { concatMap, from, toArray, of } from 'rxjs';
import { environment } from '../../../../environments/environment.development';

@Component({
  selector: 'app-edit-entry',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './edit-entry.html'
})
export class EditEntryComponent implements OnInit {
  private fb = inject(FormBuilder);
  private entryService = inject(AdminEntryService);
  private techService = inject(TechnologyService);
  private cdr = inject(ChangeDetectorRef);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);

  entryId!: number;
  entryName:string = '';
  entryForm!: FormGroup;
  isSubmitting = false;
  isLoadingData = true;

  // Estado de la imagen
  currentImageUrl: string | null = null;
  newCoverImage: File | null = null;
  imagePreviewUrl: string | null = null; // Para previsualizar la nueva imagen antes de subirla

  // Estado de Tecnologías
  technologies: any[] = [];
  selectedTechs: { technologyId: number, role: string, name: string }[] = [];

  existingDocs: any[] = [];
  docsToDelete: number[] = []; // IDs de documentos a eliminar al guardar
  
  hasExistingSummary = false;
  newSummaryDoc: any = null; // Guardará el File y metadatos si se sube uno nuevo
  newAdditionalDocs: any[] = []; // Archivos adicionales encolados

  ngOnInit() {
    this.entryId = Number(this.route.snapshot.paramMap.get('id'));
    this.entryForm = this.fb.group({
      name: ['', Validators.required],
      area: [''], // Quitamos Validators.required
      areaSecondary: [''],
      status: [''] // Quitamos Validators.required
    });

    this.loadData();
  }

  loadData() {
    // 1. Cargar Tecnologías
    this.techService.getTechnologies().subscribe(techs => this.technologies = techs);

    // 2. Cargar Datos de la Entrada (Asumiendo que tienes un método getEntryById)
    this.entryService.getEntryById(this.entryId).subscribe(entry => {
      this.entryForm.patchValue({
        name: entry.entry.name,
        area: entry.entry.area,
        areaSecondary: entry.entry.areaSecondary || '',
        status: entry.entry.status
      });
      this.entryName=String(entry.entry.name)
      this.cdr.detectChanges();

      if (entry.entry.hasCoverImage) {
        // Usamos un query param aleatorio (cache-buster) para evitar que el navegador muestre una imagen vieja en caché
        this.currentImageUrl = `${environment.apiUrl}/public/knowledge-entries/${this.entryId}/image?t=${new Date().getTime()}`;
      }
      // Mapear tecnologías existentes
      this.selectedTechs = entry.technologies || []; 
      this.cdr.detectChanges();
    });
    
    // 3. Cargar Metadatos de Documentos
    this.entryService.getEntryDocuments(this.entryId).subscribe(docs => {
      this.existingDocs = docs;
      this.hasExistingSummary = !!docs.find(d => d.docType === 'summary');
      this.isLoadingData = false;
      this.cdr.detectChanges();
    });
  }

  addAdditionalDoc(fileInput: HTMLInputElement, type: string, lang: string, depth: string, imp: string) {
    if (fileInput.files?.length && type && lang && depth && imp) {
      this.newAdditionalDocs.push({
        file: fileInput.files[0],
        docType: type,
        language: lang,
        technicalDepth: Number(depth),
        importance: Number(imp)
      });
      fileInput.value = ''; // Resetea el input
      this.cdr.detectChanges(); // Obliga a Angular a dibujar la nueva lista
    }
  }

  removeAdditionalDoc(index: number) {
    this.newAdditionalDocs.splice(index, 1);
    this.cdr.detectChanges();
  }

  onImageSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.newCoverImage = input.files[0];

      // Crear URL local para previsualizar la nueva imagen seleccionada
      const reader = new FileReader();
      reader.onload = (e) => this.imagePreviewUrl = e.target?.result as string;
      reader.readAsDataURL(this.newCoverImage);
      this.cdr.detectChanges();
    }
  }

  // --- GESTIÓN DE DOCUMENTOS (DIFERIDA) ---

  downloadDoc(docId: number, fileName: string) {
    if (!isPlatformBrowser(this.platformId)) return;

    this.entryService.downloadDocument(docId).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    });
  }

  markDocForDeletion(doc: any) {
    // Lo quitamos de la vista
    this.existingDocs = this.existingDocs.filter(d => d.id !== doc.id);
    // Lo encolamos para el bloque DELETE final
    this.docsToDelete.push(doc.id);

    if (doc.docType === 'summary') {
      this.hasExistingSummary = false;
    }
  }

  onSummarySelected(event: Event, lang: string, depth: string, imp: string) {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      if (!input.files[0].name.toLowerCase().endsWith('.md')) {
        alert('El summary debe ser .md');
        return;
      }
      this.newSummaryDoc = {
        file: input.files[0], docType: 'summary', language: lang, 
        technicalDepth: Number(depth), importance: Number(imp)
      };
    }
  }

  removeNewSummary() {
    this.newSummaryDoc = null;
  }

  // --- ORQUESTACIÓN DE GUARDADO ---

  onSubmit() {
    // VALIDACIÓN CRÍTICA: Debe existir un summary viejo, o uno nuevo encolado.
    if (!this.hasExistingSummary && !this.newSummaryDoc) {
      alert("El proyecto no puede quedarse sin un documento 'Summary'. Carga uno nuevo antes de guardar.");
      return;
    }

    if (this.entryForm.invalid) return;

    this.isSubmitting = true;

    console.log('Formulario válido, preparando payload...', this.entryForm);
    // 1. Payload de texto
    const entryDTO = {
      id: this.entryId,
      name: this.entryForm.value.name,
      area: this.entryForm.value.area,
      areaSecondary: this.entryForm.value.areaSecondary || null,
      status: this.entryForm.value.status,
      technologies: this.selectedTechs.map(t => ({ technologyId: t.technologyId, role: t.role })),
      hasCoverImage:this.entryForm.value.hasCoverImage
    };

    // FLUJO RXJS: PUT Entry -> PUT Image (opcional) -> DELETE Docs -> POST Docs
    this.entryService.updateEntry(this.entryId, entryDTO).pipe(
      // Actualizar imagen si se seleccionó una nueva
      concatMap(() => this.newCoverImage 
        ? this.entryService.updateCoverImage(this.entryId, this.newCoverImage) 
        : of(null)
      ),
      // Procesar eliminaciones de documentos encolados
      concatMap(() => from(this.docsToDelete).pipe(
        concatMap(docId => this.entryService.deleteDocument(docId)),
        toArray(), // Espera a que terminen todos los DELETE
        concatMap(() => of(null)) // Continúa el flujo
      )),
      // Procesar subidas de nuevos documentos
      concatMap(() => {
        const docsToUpload = [...this.newAdditionalDocs];
        if (this.newSummaryDoc) docsToUpload.push(this.newSummaryDoc);

        if (docsToUpload.length === 0) return of(null);

        return from(docsToUpload).pipe(
          concatMap(doc => {
            const docForm = new FormData();
            docForm.append('file', doc.file);
            docForm.append('docType', doc.docType);
            docForm.append('technicalDepth', doc.technicalDepth.toString());
            docForm.append('language', doc.language);
            docForm.append('importance', doc.importance.toString());
            // responseType: 'text' fue configurado en el servicio en el Sprint 2
            return this.entryService.uploadDocument(this.entryId, docForm);
          }),
          toArray()
        );
      })
    ).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/admin/knowledge-entries']);
      },
      error: (err) => {
        console.error(err);
        alert('Ocurrió un error guardando los cambios. Verifica la consola.');
        this.isSubmitting = false;
      }
    });
  }
}