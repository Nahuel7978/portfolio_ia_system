import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef } from '@angular/core'; // <-- Importar ChangeDetectorRef
import { CommonModule, Location, isPlatformBrowser } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { KnowledgeEntryService } from '../../core/services/knowledge-entry';
import { Title, Meta } from '@angular/platform-browser';
import { environment } from '../../../environments/environment.development';
import { MarkdownComponent } from 'ngx-markdown';
import { LucideAngularModule, ArrowLeft, Code2, FileText } from 'lucide-angular';

@Component({
  selector: 'app-detail',
  standalone: true,
  imports: [CommonModule, MarkdownComponent, LucideAngularModule],
  templateUrl: './detail.html'
})
export class DetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private entryService = inject(KnowledgeEntryService);
  private location = inject(Location);
  private titleService = inject(Title);
  private metaService = inject(Meta);
  private platformId = inject(PLATFORM_ID);
  
  // EL CAPATAZ DE ANGULAR
  private cdr = inject(ChangeDetectorRef); 

  entry: any = null;
  apiUrl = environment.apiUrl;
  isLoading = true;
  hasCover: Boolean = false;
  entryId: Number | null = null;

  readonly ArrowLeft = ArrowLeft;
  readonly Code2 = Code2;
  readonly FileText = FileText;

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      this.entryId = Number(params.get('id'));
      if (this.entryId) {
        this.isLoading = true;
        this.entry = null; // Limpiar datos anteriores
        this.cdr.detectChanges(); // Forzar dibujado de "Loading..."

        this.entryService.getEntryById(this.entryId).subscribe({
          next: (data) => {
            this.entry = data;
            this.hasCover = Boolean(this.entry.entry.hasCoverImage);
            this.isLoading = false;
            this.updateSeoTags();
            
            // LA MAGIA: Forzamos a Angular a redibujar el HTML con el Markdown
            this.cdr.detectChanges(); 

            if (isPlatformBrowser(this.platformId)) {
              setTimeout(() => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }, 50);
            }
          },
          error: () => {
            this.isLoading = false;
            this.cdr.detectChanges(); // Redibujar en caso de error
          }
        });
      }
    });
  }

  goBack() {
    this.location.back();
  }

  private updateSeoTags() {
    // Protección en caso de que data no tenga name
    const title = this.entry?.name ? `${this.entry.name} - Portfolio` : 'Detalle - Portfolio';
    this.titleService.setTitle(title);
    this.metaService.updateTag({ name: 'description', content: `Detalle: ${title}` });
  }
}