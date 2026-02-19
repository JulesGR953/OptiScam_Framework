"""
Holistic Video Analysis Example
This demonstrates the new holistic approach where the model analyzes
the entire video context along with title and description.
"""

from main import OptiScamAnalyzer


def example_holistic_analysis():
    """
    Example: Analyze a video holistically with title and description.

    The model will understand:
    - The entire video content
    - The video title
    - The video description
    - All audio transcription
    - All visible text (OCR)

    And provide a comprehensive scam detection analysis.
    """
    print("="*60)
    print("Holistic Video Scam Analysis")
    print("="*60)

    # Initialize analyzer
    analyzer = OptiScamAnalyzer()

    # Example video metadata (you would get this from YouTube, TikTok, etc.)
    video_path = 'path/to/your/video.mp4'
    video_title = 'URGENT: Your Account Has Been Suspended - Verify Now!'
    video_description = """
    Your account has been flagged for suspicious activity.
    Click the link below to verify your identity within 24 hours
    or your account will be permanently deleted.

    Verify Here: bit.ly/verify-account-urgent

    Don't wait! Limited time only!
    """

    # Run holistic analysis
    results = analyzer.analyze_video_holistic(
        video_path=video_path,
        title=video_title,
        description=video_description
    )

    # Display results
    print("\n" + "="*60)
    print("SCAM ANALYSIS RESULT")
    print("="*60)
    print(results['scam_analysis'])
    print("\n" + "="*60)
    print(f"Full report saved to: {results['output_dir']}")
    print("="*60)


def example_youtube_video_analysis():
    """
    Example: Analyze a YouTube video (you would fetch metadata via YouTube API).
    """
    from main import OptiScamAnalyzer

    analyzer = OptiScamAnalyzer()

    # Download video using yt-dlp or similar
    video_path = 'downloaded_video.mp4'

    # YouTube video metadata (fetch using YouTube Data API)
    title = "Make $10,000 Per Day With This Simple Trick!"
    description = """
    Learn the secret method millionaires don't want you to know!

    💰 Join my exclusive course: sketchy-site.com/course
    💎 Limited spots available - only 10 left!
    🚀 Start making money TODAY!

    Use code URGENT50 for 50% off (expires in 1 hour!)
    """

    # Analyze
    results = analyzer.analyze_video_holistic(
        video_path=video_path,
        title=title,
        description=description
    )

    print(f"\nScam Likelihood: {results['scam_analysis']}")


def example_minimal_metadata():
    """
    Example: Analyze video with minimal metadata (no title/description).
    """
    from main import OptiScamAnalyzer

    analyzer = OptiScamAnalyzer()

    # Analyze video without title/description
    # The model will still analyze audio and visual content
    results = analyzer.analyze_video_holistic(
        video_path='path/to/video.mp4',
        title=None,  # No title available
        description=None  # No description available
    )

    print(f"Analysis based on video content only:\n{results['scam_analysis']}")


def example_custom_config():
    """
    Example: Holistic analysis with custom configuration.
    """
    from main import OptiScamAnalyzer

    # Configure for high-quality analysis
    config = {
        'whisper_model_size': 'medium',  # Better transcription
        'use_trocr_fallback': True,      # More accurate OCR
        'sharpness_threshold': 150.0      # Only sharp frames
    }

    analyzer = OptiScamAnalyzer(config=config)

    results = analyzer.analyze_video_holistic(
        video_path='path/to/video.mp4',
        title='Investment Opportunity of a Lifetime',
        description='Guaranteed 500% returns in 30 days! Join now!'
    )

    print(results['scam_analysis'])


def example_batch_processing():
    """
    Example: Batch process multiple videos with their metadata.
    """
    from main import OptiScamAnalyzer

    analyzer = OptiScamAnalyzer()

    # List of videos with metadata
    videos = [
        {
            'path': 'video1.mp4',
            'title': 'Free iPhone Giveaway!',
            'description': 'Click here to claim your free iPhone 15 Pro Max!'
        },
        {
            'path': 'video2.mp4',
            'title': 'Account Security Alert',
            'description': 'Your account has been compromised. Verify now.'
        },
        {
            'path': 'video3.mp4',
            'title': 'Get Rich Quick Method',
            'description': 'Make $5000 per week from home with no experience!'
        }
    ]

    # Process all videos
    for video in videos:
        print(f"\nAnalyzing: {video['title']}")

        try:
            results = analyzer.analyze_video_holistic(
                video_path=video['path'],
                title=video['title'],
                description=video['description']
            )

            print(f"✓ Complete - Analysis saved to {results['output_dir']}")

        except Exception as e:
            print(f"✗ Error: {str(e)}")


def main():
    """
    Run examples (uncomment the ones you want to try).
    """
    print("OptiScam Holistic Video Analysis Examples\n")

    # Choose which example to run:

    # example_holistic_analysis()
    # example_youtube_video_analysis()
    # example_minimal_metadata()
    # example_custom_config()
    # example_batch_processing()

    print("\nDone!")


if __name__ == "__main__":
    main()
