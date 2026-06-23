import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminEntryService } from '../../../core/services/admin-entry.service';
import { environment } from '../../../../environments/environment';
import { Router, RouterLink } from  '@angular/router';
import { TechnologiesComponent } from "../technology/technology";


@Component({
  selector: 'app-knowledge-entries',
  standalone: true,
  imports: [CommonModule, RouterLink, TechnologiesComponent],
  templateUrl: './knowledge-entries.html'
})
export class KnowledgeEntriesComponent implements OnInit {
  private entryService = inject(AdminEntryService);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);
  
  activeTab: 'projects' | 'blogs' | 'technologies' = 'projects';
  entries: any[] = [];
  isLoading = false;
  apiUrl = environment.apiUrl;

  ngOnInit() {
    this.loadEntries();
  }

  setTab(tab: 'projects' | 'blogs' | 'technologies') {
    this.activeTab = tab;
    if (tab != 'technologies') {
      this.loadEntries();  
    }
  }

  loadEntries() {
    this.isLoading = true;
    const request = this.activeTab === 'projects' 
      ? this.entryService.getProjects() 
      : this.entryService.getBlogs();

    request.subscribe({
      next: (data) => {
        this.entries = data;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: () =>{
        this.isLoading = false
        this.cdr.detectChanges();
      } 
    });
     
  }

  deleteEntry(id: number, name: string) {
    // Al ser invocado por un click, el uso de window.confirm es seguro en SSR
    if (confirm(`¿Estás seguro de eliminar "${name}"? Esta acción borrará los documentos asociados.`)) {
      this.entryService.deleteEntry(id).subscribe({
        next: () => {
          this.entries = this.entries.filter(e => e.id !== id);
          this.cdr.detectChanges();
        },
        error: () => {
            alert('Ocurrió un error al eliminar la entrada.')
            this.cdr.detectChanges();
          }
      });
    }
  }

  navigate_new_entry(tab:string){
    this.router.navigate(['/admin/new-entry'],{
      queryParams: { type: tab }
    });
  }

  navigate_edit_entry(id:number){
    console.log('Navegando a editar entrada con ID:', id);
    this.router.navigate(['/admin/edit-entry/', id],{
      queryParams: { id: id }
    }
    );

  }

}