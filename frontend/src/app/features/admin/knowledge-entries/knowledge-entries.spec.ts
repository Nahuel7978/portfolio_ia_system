import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KnowledgeEntries } from './knowledge-entries';

describe('KnowledgeEntries', () => {
  let component: KnowledgeEntries;
  let fixture: ComponentFixture<KnowledgeEntries>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [KnowledgeEntries],
    }).compileComponents();

    fixture = TestBed.createComponent(KnowledgeEntries);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
