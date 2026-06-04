import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EntriesForm } from './entries-form';

describe('EntriesForm', () => {
  let component: EntriesForm;
  let fixture: ComponentFixture<EntriesForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EntriesForm],
    }).compileComponents();

    fixture = TestBed.createComponent(EntriesForm);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
