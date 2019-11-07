import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import {} from 'jasmine';

import { PlaybookArgumentComponent } from './playbook.argument.component';
import { KeysPipe } from '../pipes/keys.pipe';
import { plainToClass } from 'class-transformer';
import { Argument } from '../models/playbook/argument';
import { Workflow } from '../models/playbook/workflow';

describe('PlaybookArgumentComponent', () => {
	let comp: PlaybookArgumentComponent;
	let fixture: ComponentFixture<PlaybookArgumentComponent>;

	/**
	 * async beforeEach
	 */
	beforeEach(async(() => {
		TestBed.configureTestingModule({
			declarations: [PlaybookArgumentComponent, KeysPipe],
			schemas: [NO_ERRORS_SCHEMA],
			providers: [],
		})
			.compileComponents();
	}));

	/**
	 * Synchronous beforeEach
	 */
	beforeEach(() => {
		fixture = TestBed.createComponent(PlaybookArgumentComponent);
		comp = fixture.componentInstance;

		comp.id = 0;
		comp.loadedWorkflow = plainToClass(Workflow, {
			id: '12345',
			name: 'TestWorkflow',
			actions: [
				{
					id: '55555',
					name: 'test action',
					position: { x: 0, y: 0 },
					app_name: 'TestApp',
					action_name: 'TestActon',
					arguments: [ comp.argument ],
				},
			],
			branches: [],
			start: '55555',
		});
	});

	// it('should properly add an array item', () => {
	// 	comp.argument = plainToClass(Argument, {
	// 		name: 'test',
	// 		all_errors: [],
	// 		value: [],
	// 	});
	// 	comp.parameterApi = {
	// 		name: 'test',
	// 		schema: { type: 'array' },
	// 	};

	// 	fixture.detectChanges();
	// 	comp.selectedType = 'string';
	// 	comp.addItem();
	// 	fixture.detectChanges();
	// 	expect(comp.argument.value).toEqual(['']);
	// 	comp.selectedType = 'number';
	// 	comp.addItem();
	// 	fixture.detectChanges();
	// 	expect(comp.argument.value).toEqual(['', null]);
	// 	comp.selectedType = 'boolean';
	// 	comp.addItem();
	// 	fixture.detectChanges();
	// 	expect(comp.argument.value).toEqual(['', null, false]);
	// 	const els = fixture.debugElement.queryAll(By.css('.arrayItem'));
	// 	expect(els.length).toEqual(3);
	// });

	// it('should properly move array items', fakeAsync(() => {
	// 	comp.argument = plainToClass(Argument, {
	// 		name: 'test',
	// 		has_errors: false,
	// 		value: ['first', 'second', 'third', 'fourth', 'fifth'],
	// 	});
	// 	comp.parameterApi = {
	// 		name: 'test',
	// 		description: 'test',
	// 		schema: { type: 'array' },
	// 	};

	// 	tick();
	// 	fixture.detectChanges();
	// 	let els = fixture.debugElement.queryAll(By.css('.arrayItem'));
	// 	expect(els.length).toEqual(5);
	// 	const idToMove = 1;
	// 	comp.moveDown(idToMove);
	// 	expect(comp.argument.value[idToMove]).toEqual('third');
	// 	expect(comp.argument.value[idToMove + 1]).toEqual('second');
	// 	// TODO: figure out why input changes aren't happening
	// 	// fixture.detectChanges();
	// 	// els = fixture.debugElement.queryAll(By.css('.arrayItem'));
	// 	// let el = els[idToMove].query(By.css('input'));
	// 	// console.log(el.nativeElement.value);
	// 	// expect(el.nativeElement.value).toEqual('third');
	// }));
});
