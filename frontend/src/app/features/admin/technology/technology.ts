import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TechnologyService } from '../../../core/services/technology.service';
import { Technology } from '../../../core/models/technology.interface';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-technologies',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './technology.html'
})
export class TechnologiesComponent implements OnInit {
  private techService = inject(TechnologyService);
  private fb = inject(FormBuilder);

  technologies: Technology[] = [];
  isLoading = false;
  isSubmitting = false;
  errorMessage = '';
  successMessage = '';

  // Lista estricta que coincide con el CHECK constraint de PostgreSQL
  readonly categories = [
    'language', 'framework', 'library', 'tool', 
    'algorithm', 'infrastructure', 'platform'
  ];

  techForm: FormGroup = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(50)]],
    category: ['', Validators.required]
  });

  ngOnInit() {
    this.loadTechnologies();
  }

  loadTechnologies() {
    this.isLoading = true;
    this.techService.getTechnologies().subscribe({
      next: (data) => {
        this.technologies = data;
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Error al cargar las tecnologías.';
        this.isLoading = false;
      }
    });
  }

  onSubmit() {
    if (this.techForm.invalid) {
      this.techForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.techService.createTechnology(this.techForm.getRawValue()).subscribe({
      next: (newTech) => {
        this.technologies.push(newTech); // Actualiza la vista inmediatamente
        this.successMessage = 'Tecnología agregada con éxito.';
        this.techForm.reset();
        this.isSubmitting = false;
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (err: HttpErrorResponse) => {
        this.isSubmitting = false;
        if (err.status === 409 || err.status === 400) {
          this.errorMessage = 'La tecnología ya existe o los datos son inválidos.';
        } else {
          this.errorMessage = 'Ocurrió un error al guardar la tecnología.';
        }
      }
    });
  }
}