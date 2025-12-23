"""
Comparative Analysis Module for Multi-App Privacy Policy Comparison
Enables cross-app statistical analysis, benchmarking, and pattern detection
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime
import scipy.stats as stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from src.utils.logger import get_logger

logger = get_logger()


class ComparativeAnalyzer:
    """Analyze multiple privacy policies for comparative insights"""

    def __init__(self, analyses: List[Dict]):
        """
        Initialize comparative analyzer

        Args:
            analyses: List of complete analysis results (from JSON files)
        """
        self.analyses = analyses
        self.num_apps = len(analyses)

        logger.info(f"Initialized comparative analyzer with {self.num_apps} apps")

        # Extract metrics for analysis
        self.metrics = self._extract_metrics()

    def _extract_metrics(self) -> Dict:
        """Extract key metrics from all analyses"""
        metrics = {
            'app_names': [],
            'urls': [],
            'overall_scores': [],
            'transparency_scores': [],
            'confidence_scores': [],
            'category_scores': defaultdict(list),
            'red_flags': [],
            'red_flag_counts': [],
            'positive_practices': [],
            'missing_info': [],
            'vague_language': [],
            'compliance_flags': {
                'hipaa_mentioned': [],
                'gdpr_mentioned': [],
                'business_associate_agreement': []
            },
            'retention_specified': [],
            'readability_scores': [],
            'timestamps': []
        }

        for analysis in self.analyses:
            # Basic info
            metrics['app_names'].append(analysis.get('app_name', 'Unknown'))
            metrics['urls'].append(analysis.get('url', ''))

            # Get analysis data
            analysis_data = analysis.get('analysis', {})
            scoring_data = analysis.get('scoring', {})

            # Overall scores
            metrics['overall_scores'].append(scoring_data.get('overall_score', 0))
            metrics['transparency_scores'].append(analysis_data.get('overall_transparency_score', 0))
            metrics['confidence_scores'].append(analysis_data.get('confidence_score', 0))

            # Category scores
            for category in ['data_collection', 'data_usage', 'third_party_sharing',
                           'data_retention', 'user_rights', 'security_measures',
                           'compliance', 'older_adult_considerations']:
                score = analysis_data.get(category, {}).get('score', 0)
                metrics['category_scores'][category].append(score)

            # Red flags
            red_flags = scoring_data.get('red_flags', [])
            metrics['red_flags'].append(red_flags)
            metrics['red_flag_counts'].append(len(red_flags))

            # Positive practices
            metrics['positive_practices'].append(
                analysis_data.get('positive_practices', [])
            )

            # Missing information
            metrics['missing_info'].append(
                analysis_data.get('missing_information', [])
            )

            # Vague language
            metrics['vague_language'].append(
                analysis_data.get('vague_language_examples', [])
            )

            # Compliance
            compliance = analysis_data.get('compliance', {})
            metrics['compliance_flags']['hipaa_mentioned'].append(
                compliance.get('hipaa_mentioned', False)
            )
            metrics['compliance_flags']['gdpr_mentioned'].append(
                compliance.get('gdpr_mentioned', False)
            )
            metrics['compliance_flags']['business_associate_agreement'].append(
                bool(compliance.get('business_associate_agreement', '').strip())
            )

            # Retention
            retention = analysis_data.get('data_retention', {})
            metrics['retention_specified'].append(
                retention.get('duration_specified', False)
            )

            # Readability
            older_adult = analysis_data.get('older_adult_considerations', {})
            readability = older_adult.get('readability_score', 'Unknown')
            metrics['readability_scores'].append(readability)

            # Timestamp
            metadata = analysis_data.get('metadata', {})
            metrics['timestamps'].append(
                metadata.get('analysis_date', datetime.now().isoformat())
            )

        return metrics

    def calculate_statistics(self) -> Dict:
        """Calculate comprehensive statistics across all apps"""
        logger.info("Calculating comparative statistics")

        stats_results = {
            'summary': {
                'total_apps': self.num_apps,
                'analysis_date_range': self._get_date_range(),
            },
            'overall_risk': self._calculate_metric_stats(self.metrics['overall_scores']),
            'transparency': self._calculate_metric_stats(self.metrics['transparency_scores']),
            'confidence': self._calculate_metric_stats(self.metrics['confidence_scores']),
            'category_stats': {},
            'red_flag_stats': self._analyze_red_flags(),
            'compliance_stats': self._analyze_compliance(),
            'gap_analysis': self._perform_gap_analysis(),
            'correlations': self._calculate_correlations(),
            'rankings': self._generate_rankings(),
            'clusters': self._perform_clustering()
        }

        # Category-specific statistics
        for category, scores in self.metrics['category_scores'].items():
            stats_results['category_stats'][category] = self._calculate_metric_stats(scores)

        return stats_results

    def _calculate_metric_stats(self, values: List[float]) -> Dict:
        """Calculate statistics for a metric"""
        if not values:
            return {}

        values_array = np.array(values)

        return {
            'mean': float(np.mean(values_array)),
            'median': float(np.median(values_array)),
            'std': float(np.std(values_array)),
            'min': float(np.min(values_array)),
            'max': float(np.max(values_array)),
            'percentiles': {
                '25': float(np.percentile(values_array, 25)),
                '50': float(np.percentile(values_array, 50)),
                '75': float(np.percentile(values_array, 75)),
                '90': float(np.percentile(values_array, 90))
            }
        }

    def _get_date_range(self) -> Dict:
        """Get date range of analyses"""
        timestamps = [t for t in self.metrics['timestamps'] if t]
        if not timestamps:
            return {'earliest': None, 'latest': None}

        return {
            'earliest': min(timestamps),
            'latest': max(timestamps)
        }

    def _analyze_red_flags(self) -> Dict:
        """Analyze red flag patterns across apps"""
        all_flags = []
        flag_by_category = defaultdict(list)
        flag_by_severity = defaultdict(int)

        for app_flags in self.metrics['red_flags']:
            for flag in app_flags:
                if isinstance(flag, dict):
                    desc = flag.get('description', str(flag))
                    category = flag.get('category', 'Unknown')
                    severity = flag.get('severity', 'unknown')

                    all_flags.append(desc)
                    flag_by_category[category].append(desc)
                    flag_by_severity[severity] += 1
                else:
                    all_flags.append(str(flag))

        # Count frequencies
        flag_counter = Counter(all_flags)

        return {
            'total_flags': len(all_flags),
            'unique_flags': len(set(all_flags)),
            'avg_per_app': len(all_flags) / self.num_apps if self.num_apps > 0 else 0,
            'most_common': [
                {'flag': flag, 'count': count, 'percentage': (count / self.num_apps) * 100}
                for flag, count in flag_counter.most_common(10)
            ],
            'by_severity': dict(flag_by_severity),
            'by_category': {
                cat: len(flags) for cat, flags in flag_by_category.items()
            }
        }

    def _analyze_compliance(self) -> Dict:
        """Analyze compliance patterns"""
        hipaa_count = sum(self.metrics['compliance_flags']['hipaa_mentioned'])
        gdpr_count = sum(self.metrics['compliance_flags']['gdpr_mentioned'])
        baa_count = sum(self.metrics['compliance_flags']['business_associate_agreement'])
        retention_count = sum(self.metrics['retention_specified'])

        return {
            'hipaa_mentioned': {
                'count': hipaa_count,
                'percentage': (hipaa_count / self.num_apps) * 100
            },
            'gdpr_mentioned': {
                'count': gdpr_count,
                'percentage': (gdpr_count / self.num_apps) * 100
            },
            'business_associate_agreement': {
                'count': baa_count,
                'percentage': (baa_count / self.num_apps) * 100
            },
            'retention_period_specified': {
                'count': retention_count,
                'percentage': (retention_count / self.num_apps) * 100
            }
        }

    def _perform_gap_analysis(self) -> Dict:
        """Identify common gaps across all apps"""
        # Collect all missing information
        all_missing = []
        for missing_list in self.metrics['missing_info']:
            all_missing.extend(missing_list)

        missing_counter = Counter(all_missing)

        return {
            'common_gaps': [
                {
                    'item': item,
                    'count': count,
                    'percentage': (count / self.num_apps) * 100
                }
                for item, count in missing_counter.most_common(15)
            ],
            'apps_with_deletion_rights': self._count_feature('deletion_rights'),
            'apps_with_data_export': self._count_feature('portability'),
            'apps_with_opt_out': self._count_feature('opt_out_mechanisms')
        }

    def _count_feature(self, feature_key: str) -> Dict:
        """Count how many apps have a specific feature"""
        count = 0
        for analysis in self.analyses:
            analysis_data = analysis.get('analysis', {})
            user_rights = analysis_data.get('user_rights', {})
            feature_value = user_rights.get(feature_key, '')

            # Check if feature is meaningfully present
            if feature_value and len(str(feature_value).strip()) > 5:
                count += 1

        return {
            'count': count,
            'percentage': (count / self.num_apps) * 100
        }

    def _calculate_correlations(self) -> Dict:
        """Calculate correlations between metrics"""
        correlations = {}

        # Correlation between HIPAA mention and security score
        if len(self.metrics['compliance_flags']['hipaa_mentioned']) > 2:
            hipaa_binary = [1 if x else 0 for x in self.metrics['compliance_flags']['hipaa_mentioned']]
            security_scores = self.metrics['category_scores'].get('security_measures', [])

            if len(security_scores) == len(hipaa_binary):
                corr, pval = stats.pointbiserialr(hipaa_binary, security_scores)
                correlations['hipaa_vs_security'] = {
                    'correlation': float(corr),
                    'p_value': float(pval),
                    'significant': pval < 0.05
                }

        # Correlation between transparency and overall risk
        if len(self.metrics['transparency_scores']) > 2:
            corr, pval = stats.pearsonr(
                self.metrics['transparency_scores'],
                self.metrics['overall_scores']
            )
            correlations['transparency_vs_risk'] = {
                'correlation': float(corr),
                'p_value': float(pval),
                'significant': pval < 0.05
            }

        return correlations

    def _generate_rankings(self) -> Dict:
        """Generate rankings for all apps"""
        rankings = {
            'overall_risk': self._rank_by_metric(
                self.metrics['overall_scores'],
                higher_is_better=True
            ),
            'transparency': self._rank_by_metric(
                self.metrics['transparency_scores'],
                higher_is_better=True
            ),
            'category_rankings': {}
        }

        # Category-specific rankings
        for category, scores in self.metrics['category_scores'].items():
            rankings['category_rankings'][category] = self._rank_by_metric(
                scores,
                higher_is_better=True
            )

        return rankings

    def _rank_by_metric(self, values: List[float], higher_is_better: bool = True) -> List[Dict]:
        """Rank apps by a specific metric"""
        if not values:
            return []

        # Create list of (app_name, value) tuples
        app_values = list(zip(self.metrics['app_names'], values))

        # Sort
        app_values.sort(key=lambda x: x[1], reverse=higher_is_better)

        # Add ranks
        ranked = []
        for rank, (app_name, value) in enumerate(app_values, 1):
            # Calculate percentile
            percentile = stats.percentileofscore(values, value)

            ranked.append({
                'rank': rank,
                'app_name': app_name,
                'value': float(value),
                'percentile': float(percentile)
            })

        return ranked

    def _perform_clustering(self) -> Dict:
        """Perform clustering analysis to group similar apps"""
        if self.num_apps < 3:
            return {'clusters': [], 'note': 'Insufficient data for clustering'}

        # Prepare feature matrix
        features = []
        for i in range(self.num_apps):
            app_features = [
                self.metrics['overall_scores'][i],
                self.metrics['transparency_scores'][i],
                self.metrics['red_flag_counts'][i],
            ]

            # Add category scores
            for category in ['data_collection', 'data_usage', 'third_party_sharing',
                           'data_retention', 'user_rights', 'security_measures']:
                app_features.append(self.metrics['category_scores'][category][i])

            features.append(app_features)

        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Determine optimal number of clusters (2-4 for small datasets)
        n_clusters = min(3, max(2, self.num_apps // 2))

        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features_scaled)

        # Organize results
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[int(label)].append({
                'app_name': self.metrics['app_names'][i],
                'overall_score': self.metrics['overall_scores'][i]
            })

        return {
            'n_clusters': n_clusters,
            'clusters': [
                {
                    'cluster_id': cluster_id,
                    'size': len(apps),
                    'apps': apps,
                    'avg_score': np.mean([app['overall_score'] for app in apps])
                }
                for cluster_id, apps in clusters.items()
            ]
        }

    def identify_best_practices(self) -> Dict:
        """Identify best-in-class practices for each category"""
        logger.info("Identifying best practices")

        best_practices = {}

        # For each category, find top performers
        for category, scores in self.metrics['category_scores'].items():
            if not scores:
                continue

            # Find apps with scores in top 25%
            threshold = np.percentile(scores, 75)
            top_performers = []

            for i, score in enumerate(scores):
                if score >= threshold:
                    app_name = self.metrics['app_names'][i]
                    analysis = self.analyses[i].get('analysis', {})
                    category_data = analysis.get(category, {})

                    top_performers.append({
                        'app_name': app_name,
                        'score': float(score),
                        'positive_aspects': category_data.get('positive_aspects', [])
                    })

            best_practices[category] = top_performers

        return best_practices

    def identify_worst_practices(self) -> Dict:
        """Identify concerning practices that need attention"""
        logger.info("Identifying worst practices")

        worst_practices = {}

        # For each category, find bottom performers
        for category, scores in self.metrics['category_scores'].items():
            if not scores:
                continue

            # Find apps with scores in bottom 25%
            threshold = np.percentile(scores, 25)
            poor_performers = []

            for i, score in enumerate(scores):
                if score <= threshold:
                    app_name = self.metrics['app_names'][i]
                    analysis = self.analyses[i].get('analysis', {})
                    category_data = analysis.get(category, {})

                    poor_performers.append({
                        'app_name': app_name,
                        'score': float(score),
                        'concerns': category_data.get('concerns', [])
                    })

            worst_practices[category] = poor_performers

        return worst_practices

    def extract_research_quotes(self) -> Dict:
        """Extract all quotable findings organized by theme"""
        logger.info("Extracting research quotes")

        quotes_by_theme = defaultdict(list)

        for analysis in self.analyses:
            app_name = analysis.get('app_name', 'Unknown')
            analysis_data = analysis.get('analysis', {})

            quotable = analysis_data.get('quotable_findings', [])
            for finding in quotable:
                if isinstance(finding, dict):
                    category = finding.get('category', 'General')
                    quotes_by_theme[category].append({
                        'app': app_name,
                        'finding': finding.get('finding', ''),
                        'quote': finding.get('quote', ''),
                        'significance': finding.get('significance', '')
                    })

        return dict(quotes_by_theme)

    def generate_comparative_report(self) -> Dict:
        """Generate comprehensive comparative analysis report"""
        logger.info("Generating comprehensive comparative report")

        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'num_apps_analyzed': self.num_apps,
                'app_names': self.metrics['app_names']
            },
            'statistics': self.calculate_statistics(),
            'best_practices': self.identify_best_practices(),
            'worst_practices': self.identify_worst_practices(),
            'research_quotes': self.extract_research_quotes(),
            'recommendations': self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate policy recommendations based on findings"""
        recommendations = []

        # Check HIPAA compliance
        hipaa_pct = (sum(self.metrics['compliance_flags']['hipaa_mentioned']) / self.num_apps) * 100
        if hipaa_pct < 50:
            recommendations.append(
                f"Only {hipaa_pct:.1f}% of apps explicitly mention HIPAA compliance. "
                "Healthcare apps should clearly state HIPAA compliance status."
            )

        # Check retention policies
        retention_pct = (sum(self.metrics['retention_specified']) / self.num_apps) * 100
        if retention_pct < 70:
            recommendations.append(
                f"Only {retention_pct:.1f}% of apps specify data retention periods. "
                "Clear retention policies should be mandatory for healthcare data."
            )

        # Check readability
        complex_count = sum(1 for r in self.metrics['readability_scores'] if 'college' in str(r).lower())
        if complex_count > self.num_apps * 0.5:
            recommendations.append(
                f"{complex_count} apps use college-level language. "
                "Privacy policies should be written at an 8th-grade reading level for accessibility."
            )

        # Check average transparency
        avg_transparency = np.mean(self.metrics['transparency_scores']) if self.metrics['transparency_scores'] else 0
        if avg_transparency < 60:
            recommendations.append(
                f"Average transparency score is {avg_transparency:.1f}/100. "
                "Industry should improve clarity and specificity in privacy policies."
            )

        return recommendations


def load_analyses_from_directory(directory: str) -> List[Dict]:
    """
    Load all JSON analysis files from a directory

    Args:
        directory: Path to directory containing JSON files

    Returns:
        List of analysis dictionaries
    """
    analyses = []
    dir_path = Path(directory)

    if not dir_path.exists():
        logger.error(f"Directory not found: {directory}")
        return analyses

    json_files = list(dir_path.glob("*_report_*.json"))
    logger.info(f"Found {len(json_files)} JSON reports in {directory}")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                analyses.append(data)
                logger.debug(f"Loaded: {json_file.name}")
        except Exception as e:
            logger.error(f"Failed to load {json_file}: {e}")

    logger.info(f"Successfully loaded {len(analyses)} analyses")
    return analyses
