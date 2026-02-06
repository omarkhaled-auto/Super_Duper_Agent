import { Routes } from '@angular/router';

export const EVALUATION_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./comparable-sheet.component').then(m => m.ComparableSheetComponent),
    title: 'Evaluation - Bayan'
  },
  {
    path: 'technical',
    loadComponent: () => import('./technical-scoring.component').then(m => m.TechnicalScoringComponent),
    title: 'Technical Scoring - Bayan'
  },
  {
    path: 'technical-summary',
    loadComponent: () => import('./technical-summary.component').then(m => m.TechnicalSummaryComponent),
    title: 'Technical Summary - Bayan'
  },
  {
    path: 'scorecard',
    loadComponent: () => import('./combined-scorecard.component').then(m => m.CombinedScorecardComponent),
    title: 'Combined Scorecard - Bayan'
  },
  {
    path: 'setup',
    loadComponent: () => import('./evaluation-setup.component').then(m => m.EvaluationSetupComponent),
    title: 'Evaluation Setup - Bayan'
  }
];
