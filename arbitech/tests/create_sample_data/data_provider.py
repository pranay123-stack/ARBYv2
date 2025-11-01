"""
Sample Data Provider for VLM Testing

Provides utilities to load and manage sample betting interface images and ground truth data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image


class SampleDataProvider:
    """Provider for sample betting interface data used in VLM testing."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the sample data provider.
        
        Args:
            base_path: Path to the sample data directory. If None, uses default location.
        """
        if base_path is None:
            base_path = Path(__file__).parent
            
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)
        
        # Validate directory structure
        self._validate_directory_structure()
        
    def _validate_directory_structure(self):
        """Validate that required directories exist."""
        required_dirs = [
            "betting_interfaces",
            "ground_truth_data", 
            "test_scenarios",
            "metadata"
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                
        if missing_dirs:
            self.logger.warning(f"Missing sample data directories: {missing_dirs}")
            
    def get_test_images(self, 
                       bookmaker: Optional[str] = None,
                       sport: Optional[str] = None, 
                       difficulty: Optional[str] = None) -> List[str]:
        """Get list of test images matching criteria.
        
        Args:
            bookmaker: Filter by bookmaker name
            sport: Filter by sport
            difficulty: Filter by difficulty level
            
        Returns:
            List of image filenames
        """
        images_dir = self.base_path / "betting_interfaces"
        
        if not images_dir.exists():
            self.logger.warning(f"Images directory not found: {images_dir}")
            return []
            
        # Get all PNG files (mock images)
        all_images = list(images_dir.glob("*.png"))
        image_names = [img.name for img in all_images]
        
        # Apply filters based on ground truth data
        if bookmaker or sport or difficulty:
            filtered_images = []
            
            for image_name in image_names:
                ground_truth = self.get_ground_truth_data(image_name)
                if ground_truth:
                    matches = True
                    
                    if bookmaker and ground_truth.get("bookmaker", "").lower() != bookmaker.lower():
                        matches = False
                        
                    if sport and ground_truth.get("sport", "").lower() != sport.lower():
                        matches = False
                        
                    if difficulty and ground_truth.get("extraction_difficulty", "") != difficulty:
                        matches = False
                        
                    if matches:
                        filtered_images.append(image_name)
                        
            return filtered_images
            
        return image_names
        
    def get_ground_truth_data(self, image_filename: str) -> Optional[Dict[str, Any]]:
        """Get ground truth data for an image.
        
        Args:
            image_filename: Name of the image file
            
        Returns:
            Ground truth data dictionary or None if not found
        """
        # Try to find matching ground truth file
        ground_truth_dir = self.base_path / "ground_truth_data"
        
        if not ground_truth_dir.exists():
            self.logger.warning(f"Ground truth directory not found: {ground_truth_dir}")
            return None
            
        # Look for files that might match this image
        image_base = Path(image_filename).stem
        
        # Try exact match first
        potential_files = [
            f"{image_base}.json",  # Exact match
        ]
        
        # Add common suffix variations
        if not any((ground_truth_dir / f).exists() for f in potential_files):
            # Look for any file that references this image
            for json_file in ground_truth_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        
                    if data.get("image_filename") == image_filename:
                        return data
                        
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    self.logger.warning(f"Error reading ground truth file {json_file}: {e}")
                    continue
                    
        # Try loading by filename pattern
        for potential_file in potential_files:
            file_path = ground_truth_dir / potential_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    self.logger.warning(f"Error reading ground truth file {file_path}: {e}")
                    continue
                    
        self.logger.info(f"No ground truth found for image: {image_filename}")
        return None
        
    def load_test_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Load a test scenario configuration.
        
        Args:
            scenario_name: Name of the scenario (without .json extension)
            
        Returns:
            Scenario configuration dictionary or None if not found
        """
        scenario_dir = self.base_path / "test_scenarios"
        
        if not scenario_dir.exists():
            self.logger.warning(f"Test scenarios directory not found: {scenario_dir}")
            return None
            
        scenario_file = scenario_dir / f"{scenario_name}.json"
        
        if not scenario_file.exists():
            self.logger.warning(f"Scenario file not found: {scenario_file}")
            return None
            
        try:
            with open(scenario_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Error reading scenario file {scenario_file}: {e}")
            return None
            
    def get_dataset_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics and metadata.
        
        Returns:
            Dictionary containing dataset statistics
        """
        metadata_dir = self.base_path / "metadata"
        
        if not metadata_dir.exists():
            self.logger.warning(f"Metadata directory not found: {metadata_dir}")
            return {}
            
        stats_file = metadata_dir / "dataset_statistics.json"
        
        if not stats_file.exists():
            self.logger.warning(f"Statistics file not found: {stats_file}")
            return {}
            
        try:
            with open(stats_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Error reading statistics file {stats_file}: {e}")
            return {}
            
    def create_mock_image(self, 
                         filename: str,
                         size: Tuple[int, int] = (800, 600),
                         color: Tuple[int, int, int] = (255, 255, 255)) -> Path:
        """Create a mock betting interface image for testing.
        
        Args:
            filename: Name for the mock image file
            size: Image dimensions (width, height)
            color: RGB color tuple for the image background
            
        Returns:
            Path to the created image file
        """
        images_dir = self.base_path / "betting_interfaces"
        images_dir.mkdir(exist_ok=True)
        
        image_path = images_dir / filename
        
        # Create a simple colored image as placeholder
        img = Image.new('RGB', size, color)
        
        # Add some basic text as placeholder content
        try:
            from PIL import ImageDraw, ImageFont
            
            draw = ImageDraw.Draw(img)
            
            # Use default font
            font = ImageFont.load_default()
            
            # Add mock text content
            draw.text((10, 10), "Mock Betting Interface", fill=(0, 0, 0), font=font)
            draw.text((10, 30), f"Image: {filename}", fill=(0, 0, 0), font=font)
            draw.text((10, 50), "Mock odds display", fill=(0, 0, 0), font=font)
            draw.text((10, 70), "Team A vs Team B", fill=(0, 0, 0), font=font)
            draw.text((10, 90), "1.95  3.20  4.10", fill=(0, 0, 0), font=font)
            
        except ImportError:
            self.logger.warning("PIL not available for text overlay, creating plain image")
            
        img.save(image_path)
        self.logger.info(f"Created mock image: {image_path}")
        
        return image_path
        
    def list_available_scenarios(self) -> List[str]:
        """List all available test scenarios.
        
        Returns:
            List of scenario names
        """
        scenario_dir = self.base_path / "test_scenarios"
        
        if not scenario_dir.exists():
            return []
            
        scenarios = []
        for json_file in scenario_dir.glob("*.json"):
            scenarios.append(json_file.stem)
            
        return sorted(scenarios)
        
    def get_bookmaker_list(self) -> List[str]:
        """Get list of all bookmakers in the dataset.
        
        Returns:
            List of bookmaker names
        """
        stats = self.get_dataset_statistics()
        bookmaker_coverage = stats.get("bookmaker_coverage", {})
        
        return list(bookmaker_coverage.keys())
        
    def get_sport_list(self) -> List[str]:
        """Get list of all sports in the dataset.
        
        Returns:
            List of sport names
        """
        stats = self.get_dataset_statistics()
        sport_coverage = stats.get("sport_coverage", {})
        
        return list(sport_coverage.keys())
        
    def get_difficulty_levels(self) -> List[str]:
        """Get list of all difficulty levels in the dataset.
        
        Returns:
            List of difficulty level names
        """
        stats = self.get_dataset_statistics()
        difficulty_levels = stats.get("difficulty_levels", {})
        
        return list(difficulty_levels.keys())
        
    def validate_sample_data(self) -> Dict[str, Any]:
        """Validate the completeness and consistency of sample data.
        
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "statistics": {}
        }
        
        # Check directory structure
        required_dirs = [
            "betting_interfaces",
            "ground_truth_data",
            "test_scenarios", 
            "metadata"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                validation_results["issues"].append(f"Missing directory: {dir_name}")
                validation_results["is_valid"] = False
                
        # Check for images
        images = self.get_test_images()
        validation_results["statistics"]["total_images"] = len(images)
        
        if len(images) == 0:
            validation_results["warnings"].append("No test images found")
            
        # Check for ground truth data
        ground_truth_count = 0
        for image in images[:10]:  # Check first 10 images
            if self.get_ground_truth_data(image):
                ground_truth_count += 1
                
        validation_results["statistics"]["ground_truth_coverage"] = {
            "checked_images": min(10, len(images)),
            "images_with_ground_truth": ground_truth_count,
            "coverage_rate": ground_truth_count / min(10, len(images)) if images else 0
        }
        
        # Check for test scenarios
        scenarios = self.list_available_scenarios()
        validation_results["statistics"]["total_scenarios"] = len(scenarios)
        
        if len(scenarios) == 0:
            validation_results["warnings"].append("No test scenarios found")
            
        # Check dataset statistics
        stats = self.get_dataset_statistics()
        if not stats:
            validation_results["warnings"].append("No dataset statistics found")
        else:
            validation_results["statistics"]["dataset_quality"] = stats.get("quality_metrics", {})
            
        return validation_results
        
    def print_dataset_summary(self):
        """Print a summary of the dataset."""
        print("VLM Betting Interface Test Dataset Summary")
        print("=" * 45)
        
        stats = self.get_dataset_statistics()
        if not stats:
            print("No dataset statistics available")
            return
            
        dataset_info = stats.get("dataset_info", {})
        print(f"Dataset: {dataset_info.get('name', 'Unknown')}")
        print(f"Version: {dataset_info.get('version', 'Unknown')}")
        print(f"Total Images: {dataset_info.get('total_images', 0)}")
        print(f"Total Ground Truth Files: {dataset_info.get('total_ground_truth_files', 0)}")
        print(f"Total Test Scenarios: {dataset_info.get('total_scenarios', 0)}")
        
        print("\nBookmaker Coverage:")
        bookmaker_coverage = stats.get("bookmaker_coverage", {})
        for bookmaker, data in bookmaker_coverage.items():
            print(f"  {bookmaker}: {data.get('image_count', 0)} images")
            
        print("\nSport Coverage:")
        sport_coverage = stats.get("sport_coverage", {})
        for sport, data in sport_coverage.items():
            print(f"  {sport}: {data.get('image_count', 0)} images")
            
        print("\nDifficulty Levels:")
        difficulty_levels = stats.get("difficulty_levels", {})
        for difficulty, data in difficulty_levels.items():
            print(f"  {difficulty}: {data.get('image_count', 0)} images")
            
        quality_metrics = stats.get("quality_metrics", {})
        if quality_metrics:
            print(f"\nDataset Quality Score: {quality_metrics.get('overall_dataset_quality_score', 0.0):.2f}")


# Convenience functions for quick access
def get_sample_data_provider() -> SampleDataProvider:
    """Get a sample data provider instance."""
    return SampleDataProvider()


def quick_test_images(bookmaker: Optional[str] = None, 
                     sport: Optional[str] = None) -> List[str]:
    """Quick function to get test images with optional filters."""
    provider = get_sample_data_provider()
    return provider.get_test_images(bookmaker=bookmaker, sport=sport)


def quick_ground_truth(image_filename: str) -> Optional[Dict[str, Any]]:
    """Quick function to get ground truth data for an image."""
    provider = get_sample_data_provider()
    return provider.get_ground_truth_data(image_filename)


if __name__ == "__main__":
    # Example usage
    provider = SampleDataProvider()
    
    # Print dataset summary
    provider.print_dataset_summary()
    
    print("\n" + "=" * 50)
    print("Available Test Scenarios:")
    scenarios = provider.list_available_scenarios()
    for scenario in scenarios:
        print(f"  - {scenario}")
        
    print("\n" + "=" * 50)
    print("Sample Test Images:")
    images = provider.get_test_images()[:5]
    for image in images:
        print(f"  - {image}")
        ground_truth = provider.get_ground_truth_data(image)
        if ground_truth:
            print(f"    Bookmaker: {ground_truth.get('bookmaker')}")
            print(f"    Sport: {ground_truth.get('sport')}")
            print(f"    Difficulty: {ground_truth.get('extraction_difficulty')}")
        else:
            print("    No ground truth data found")
            
    print("\n" + "=" * 50)
    print("Validation Results:")
    validation = provider.validate_sample_data()
    print(f"Valid: {validation['is_valid']}")
    print(f"Issues: {len(validation['issues'])}")
    print(f"Warnings: {len(validation['warnings'])}")
    
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
            
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")