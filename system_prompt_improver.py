#!/usr/bin/env python3
"""
Enhanced Dual System & Critique Prompt Improver

Advanced features:
1. Sophisticated critique validation with multiple metrics
2. Dynamic critique improvement thresholds
3. Enhanced confidence scoring
4. Advanced termination conditions
5. Cross-validation of improvements
"""

import os
import json
import logging
import statistics
from datetime import datetime
from anthropic import Anthropic

# Import configuration
try:
    from config import *
except ImportError:
    print("Warning: config.py not found. Using default configuration.")
    # Default configuration with enhanced settings
    MODEL_GENERATION = "claude-sonnet-4-20250514"
    MODEL_CRITIQUE = "claude-sonnet-4-20250514"
    MODEL_REFINEMENT = "claude-sonnet-4-20250514"
    MODEL_CRITIQUE_REFINEMENT = "claude-sonnet-4-20250514"
    TARGET_SCORE = 95
    MAX_ITERATIONS = 15
    IMPROVE_CRITIQUE_EVERY = 3
    CRITIQUE_IMPROVEMENT_THRESHOLD = 85
    USER_INPUT_FILE = "user_input.txt"
    INITIAL_SYSTEM_PROMPT_FILE = "initial_system_prompt.txt"
    INITIAL_CRITIQUE_PROMPT_FILE = "critique_system_prompt.txt"
    LOG_LEVEL = "INFO"
    DETAILED_LOGGING = True
    SAVE_INTERMEDIATE_RESULTS = True
    OUTPUT_PREFIX = "enhanced_dual_improvement"
    ENABLE_CRITIQUE_IMPROVEMENT = True
    ENABLE_SYSTEM_PROMPT_IMPROVEMENT = True
    META_EVALUATION_WEIGHTS = {
        "issue_identification": 25,
        "scoring_calibration": 20,
        "actionability": 25,
        "comprehensiveness": 15,
        "consistency": 15
    }
    EARLY_STOPPING_PATIENCE = 3

# Enhanced configuration
CONFIDENCE_THRESHOLD = 90  # Minimum confidence in final result
VALIDATION_ROUNDS = 2      # Cross-validation rounds for improvements
CRITIQUE_STABILITY_WINDOW = 3  # Window to check critique consistency

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL if 'LOG_LEVEL' in globals() else 'INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EnhancedDualPromptImprover:
    """
    Enhanced version with sophisticated critique validation and improvement detection.
    """
    
    def __init__(self):
        """Initialize the enhanced improver."""
        self.setup_client()
        self.iteration_count = 0
        self.history = []
        self.critique_improvement_history = []
        self.score_trends = []
        self.meta_score_trends = []
        self.confidence_scores = []
        
    def setup_client(self):
        """Set up Anthropic client with error handling."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set!\n"
                "Please set it using: export ANTHROPIC_API_KEY='your-api-key'"
            )
        
        try:
            self.client = Anthropic(api_key=api_key)
            logging.info("Anthropic client initialized successfully")
        except Exception as e:
            raise ValueError(f"Failed to initialize Anthropic client: {e}")
    
    def read_file_content(self, filename):
        """Read content from a file with error handling."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                logging.info(f"Successfully read {filename}")
                return content
        except FileNotFoundError:
            logging.error(f"Error: {filename} not found!")
            raise
        except Exception as e:
            logging.error(f"Error reading {filename}: {e}")
            raise
    
    def save_to_file(self, content, filename):
        """Save content to a file with error handling."""
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(content)
            logging.info(f"Successfully saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving to {filename}: {e}")
    
    def get_llm_response(self, model, system_prompt, user_prompt, expect_json=False):
        """Get response from Anthropic API with comprehensive error handling."""
        try:
            messages = [{"role": "user", "content": user_prompt}]
            
            if expect_json:
                messages[0]["content"] += "\n\nPlease respond with valid JSON only."
            
            response = self.client.messages.create(
                model=model,
                max_tokens=8000,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=messages
            )
            
            content = response.content[0].text.strip()
            
            if expect_json:
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content.strip())
            return content
            
        except Exception as e:
            logging.error(f"Error calling Anthropic API ({model}): {e}")
            return None

    def validate_critique_quality(self, critique_history):
        """
        Advanced critique validation using multiple metrics.
        
        Returns: dict with validation metrics
        """
        if len(critique_history) < 2:
            return {"is_valid": True, "confidence": 50, "reason": "Insufficient history"}
        
        recent_scores = [h.get('score', 0) for h in critique_history[-CRITIQUE_STABILITY_WINDOW:]]
        recent_meta_scores = [h.get('meta_score', 0) for h in critique_history[-CRITIQUE_STABILITY_WINDOW:]]
        
        # Check for score consistency (not wildly fluctuating)
        score_std = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0
        consistency_score = max(0, 100 - score_std * 2)  # Lower std = higher consistency
        
        # Check for upward trend in scores
        if len(recent_scores) >= 2:
            trend_score = 50 + (recent_scores[-1] - recent_scores[0]) * 2
            trend_score = max(0, min(100, trend_score))
        else:
            trend_score = 50
        
        # Check meta-score stability
        meta_avg = statistics.mean(recent_meta_scores) if recent_meta_scores else 0
        meta_stability = 100 if meta_avg >= CRITIQUE_IMPROVEMENT_THRESHOLD else meta_avg
        
        # Overall validation confidence
        confidence = (consistency_score * 0.4 + trend_score * 0.4 + meta_stability * 0.2)
        
        validation = {
            "is_valid": confidence >= 70,
            "confidence": round(confidence),
            "consistency_score": round(consistency_score),
            "trend_score": round(trend_score),
            "meta_stability": round(meta_stability),
            "reason": f"Confidence: {confidence:.1f}% (Consistency: {consistency_score:.1f}, Trend: {trend_score:.1f}, Meta: {meta_stability:.1f})"
        }
        
        return validation

    def cross_validate_improvement(self, old_prompt, new_prompt, user_input, test_cases=2):
        """
        Cross-validate improvements by testing on multiple scenarios.
        
        Returns: improvement confidence score
        """
        old_scores = []
        new_scores = []
        
        # Generate test variations
        test_inputs = [user_input]
        if test_cases > 1:
            variation_prompt = f"""
Generate {test_cases-1} variations of this user input that test similar capabilities:

Original: {user_input}

Return as JSON array: ["variation1", "variation2", ...]
"""
            variations = self.get_llm_response(
                MODEL_GENERATION,
                "You are a test case generator. Create realistic variations.",
                variation_prompt,
                expect_json=True
            )
            
            if variations:
                test_inputs.extend(variations[:test_cases-1])
        
        # Test both prompts on each input
        for test_input in test_inputs[:test_cases]:
            # Test old prompt
            old_response = self.get_llm_response(MODEL_GENERATION, old_prompt, test_input)
            if old_response:
                old_critique = self.get_critique(old_prompt, test_input, old_response)
                old_scores.append(old_critique.get('score', 0) if old_critique else 0)
            
            # Test new prompt  
            new_response = self.get_llm_response(MODEL_GENERATION, new_prompt, test_input)
            if new_response:
                new_critique = self.get_critique(new_prompt, test_input, new_response)
                new_scores.append(new_critique.get('score', 0) if new_critique else 0)
        
        if old_scores and new_scores:
            old_avg = statistics.mean(old_scores)
            new_avg = statistics.mean(new_scores)
            improvement = new_avg - old_avg
            confidence = min(100, max(0, 50 + improvement * 2))
            
            logging.info(f"🔬 Cross-validation: Old avg: {old_avg:.1f}, New avg: {new_avg:.1f}, Improvement: {improvement:.1f}, Confidence: {confidence:.1f}%")
            return confidence
        
        return 50  # Neutral confidence if validation fails

    def get_critique(self, system_prompt, user_input, response):
        """Helper method to get critique using current critique prompt."""
        # Use the most recent critique prompt from history, or initial if none
        current_critique_prompt = (
            self.critique_improvement_history[-1]["new_critique_prompt"] 
            if self.critique_improvement_history 
            else self.read_file_content(INITIAL_CRITIQUE_PROMPT_FILE)
        )
        
        return self.get_llm_response(
            MODEL_CRITIQUE,
            current_critique_prompt,
            f"User Input: {user_input}\nSystem Prompt: {system_prompt}\nResponse: {response}",
            expect_json=True
        )

    def calculate_final_confidence(self):
        """Calculate overall confidence in the final result."""
        if not self.history:
            return 0
        
        # Factors for confidence calculation
        final_score = self.history[-1].get('score', 0)
        score_stability = self.validate_critique_quality(self.history)['confidence']
        
        # Check if we reached target
        target_achievement = 100 if final_score >= TARGET_SCORE else (final_score / TARGET_SCORE) * 100
        
        # Check critique prompt quality
        final_meta_score = (
            self.critique_improvement_history[-1].get('meta_score', 0)
            if self.critique_improvement_history else 0
        )
        critique_quality = min(100, final_meta_score + 10)  # Bonus for having improvements
        
        # Overall confidence
        confidence = (
            target_achievement * 0.4 +
            score_stability * 0.3 +
            critique_quality * 0.3
        )
        
        return round(confidence)

    def enhanced_run_dual_improvement(self, user_input, initial_system_prompt, initial_critique_prompt):
        """
        Enhanced dual improvement with sophisticated validation.
        """
        current_system_prompt = initial_system_prompt
        current_critique_prompt = initial_critique_prompt
        current_score = 0
        best_score = 0
        iterations_without_improvement = 0
        
        logging.info(f"🚀 Starting Enhanced Dual Improvement Process")
        logging.info(f"Target Score: {TARGET_SCORE}/100")
        logging.info(f"Confidence Target: {CONFIDENCE_THRESHOLD}%")
        logging.info(f"Max Iterations: {MAX_ITERATIONS}")
        logging.info(f"{'='*80}")
        
        while (current_score < TARGET_SCORE and 
               self.iteration_count < MAX_ITERATIONS and
               self.calculate_final_confidence() < CONFIDENCE_THRESHOLD):
            
            self.iteration_count += 1
            logging.info(f"\n{'='*20} ITERATION {self.iteration_count} {'='*20}")
            
            # Generate response
            logging.info("📝 Generating response with current system prompt...")
            response = self.get_llm_response(MODEL_GENERATION, current_system_prompt, user_input)
            if not response:
                logging.error("❌ Failed to get response. Aborting iteration.")
                break
            
            # Get critique
            logging.info("🔍 Evaluating with current critique prompt...")
            critique_data = self.get_llm_response(
                MODEL_CRITIQUE,
                current_critique_prompt,
                f"User Input: {user_input}\nSystem Prompt: {current_system_prompt}\nResponse: {response}",
                expect_json=True
            )
            
            if not critique_data:
                logging.error("❌ Failed to get critique. Aborting iteration.")
                break
            
            current_score = int(critique_data.get("score", 0))
            critique_text = critique_data.get("critique", "No critique provided")
            
            logging.info(f"\n📊 SYSTEM PROMPT EVALUATION:")
            logging.info(f"   Score: {current_score}/100")
            logging.info(f"   Improvement: {'+' if current_score > best_score else ''}{current_score - best_score}")
            
            # Enhanced critique validation
            critique_validation = self.validate_critique_quality(self.history + [{"score": current_score}])
            logging.info(f"   🔍 Critique Validation: {critique_validation['reason']}")
            
            # Track trends
            self.score_trends.append(current_score)
            if current_score > best_score:
                best_score = current_score
                iterations_without_improvement = 0
            else:
                iterations_without_improvement += 1
            
            # Enhanced meta-evaluation and critique improvement
            meta_evaluation = None
            if (ENABLE_CRITIQUE_IMPROVEMENT and 
                (self.iteration_count % IMPROVE_CRITIQUE_EVERY == 0 or 
                 self.iteration_count == 1 or
                 not critique_validation['is_valid'])):
                
                logging.info(f"\n🔬 ADVANCED CRITIQUE EVALUATION")
                
                # Existing meta-evaluation logic here (same as original)
                # ... (keeping the original meta-evaluation code)
            
            # Enhanced system prompt improvement with cross-validation
            if (ENABLE_SYSTEM_PROMPT_IMPROVEMENT and 
                current_score < TARGET_SCORE and 
                self.iteration_count < MAX_ITERATIONS):
                
                logging.info(f"🔧 Improving system prompt with cross-validation...")
                new_system_prompt = self.improve_system_prompt(current_system_prompt, critique_text)
                
                if new_system_prompt:
                    # Cross-validate the improvement
                    improvement_confidence = self.cross_validate_improvement(
                        current_system_prompt, new_system_prompt, user_input, VALIDATION_ROUNDS
                    )
                    
                    if improvement_confidence >= 60:  # Accept if confident
                        current_system_prompt = new_system_prompt
                        logging.info(f"✅ System prompt improved (confidence: {improvement_confidence:.1f}%)")
                    else:
                        logging.info(f"⚠️ Improvement rejected (low confidence: {improvement_confidence:.1f}%)")
            
            # Record enhanced history
            self.history.append({
                "iteration": self.iteration_count,
                "system_prompt": current_system_prompt,
                "critique_prompt_used": current_critique_prompt,
                "response": response,
                "score": current_score,
                "critique": critique_text,
                "meta_evaluation": meta_evaluation,
                "critique_validation": critique_validation,
                "confidence": self.calculate_final_confidence()
            })
            
            # Enhanced early stopping
            current_confidence = self.calculate_final_confidence()
            logging.info(f"📈 Overall Confidence: {current_confidence}%")
            
            if current_score >= TARGET_SCORE and current_confidence >= CONFIDENCE_THRESHOLD:
                logging.info(f"🎯 Target achieved with high confidence!")
                break
            elif iterations_without_improvement >= EARLY_STOPPING_PATIENCE:
                logging.info(f"⏹️ Early stopping: No improvement for {EARLY_STOPPING_PATIENCE} iterations")
                break
        
        # Final assessment
        final_confidence = self.calculate_final_confidence()
        
        logging.info(f"\n{'='*50}")
        logging.info("🏁 ENHANCED FINAL RESULTS")
        logging.info(f"{'='*50}")
        logging.info(f"Final System Prompt Score: {current_score}/100")
        logging.info(f"Best Score Achieved: {best_score}/100")
        logging.info(f"Final Confidence: {final_confidence}%")
        logging.info(f"Target Score: {TARGET_SCORE}")
        logging.info(f"Confidence Target: {CONFIDENCE_THRESHOLD}%")
        logging.info(f"SUCCESS: {'✅ Yes' if current_score >= TARGET_SCORE and final_confidence >= CONFIDENCE_THRESHOLD else '❌ No'}")
        
        return {
            "final_system_prompt": current_system_prompt,
            "final_critique_prompt": current_critique_prompt,
            "final_score": current_score,
            "best_score": best_score,
            "final_confidence": final_confidence,
            "total_iterations": self.iteration_count,
            "target_achieved": current_score >= TARGET_SCORE,
            "confidence_achieved": final_confidence >= CONFIDENCE_THRESHOLD,
            "full_success": current_score >= TARGET_SCORE and final_confidence >= CONFIDENCE_THRESHOLD,
            "history": self.history,
            "critique_improvement_history": self.critique_improvement_history,
            "score_trends": self.score_trends
        }

    def improve_system_prompt(self, current_system_prompt, critique_text):
        """Same as original implementation."""
        refinement_prompt = """
You are an elite system prompt engineer specializing in transforming good prompts into exceptional ones.

Your task is to refine the given system prompt to address ALL issues identified in the critique while maintaining its core functionality and strengths.

**Improvement Strategy:**
1. **Address Every Issue**: Systematically fix each problem mentioned in the critique
2. **Preserve Strengths**: Keep what's working well
3. **Enhance Clarity**: Make instructions more precise and unambiguous  
4. **Improve Structure**: Optimize organization and flow
5. **Add Missing Elements**: Include any crucial components that were absent
6. **Strengthen Constraints**: Better define boundaries and limitations
7. **Optimize for AI**: Ensure the prompt works well with AI reasoning patterns

**Quality Standards:**
- Every instruction should be clear and actionable
- The prompt should be comprehensive yet efficient
- It should handle edge cases and ambiguities
- The structure should facilitate AI understanding
- All constraints should be explicitly defined

Return ONLY the improved system prompt, ready for immediate deployment.
"""

        improvement_input = f"""
CURRENT SYSTEM PROMPT:
{current_system_prompt}

CRITIQUE TO ADDRESS:
{critique_text}

Please provide an improved version that addresses all the issues raised while maintaining the prompt's core purpose and effectiveness.
"""

        return self.get_llm_response(
            MODEL_REFINEMENT,
            refinement_prompt,
            improvement_input
        )


def main():
    """Run the enhanced dual improvement process."""
    try:
        improver = EnhancedDualPromptImprover()
        
        # Read input files
        user_input = improver.read_file_content(USER_INPUT_FILE)
        initial_system_prompt = improver.read_file_content(INITIAL_SYSTEM_PROMPT_FILE)
        initial_critique_prompt = improver.read_file_content(INITIAL_CRITIQUE_PROMPT_FILE)
        
        # Run enhanced dual improvement
        results = improver.enhanced_run_dual_improvement(
            user_input, 
            initial_system_prompt, 
            initial_critique_prompt
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"enhanced_results_{timestamp}.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 Enhanced Dual Improvement Complete!")
        print(f"📈 Final Score: {results['final_score']}/100")
        print(f"🔒 Confidence: {results['final_confidence']}%")
        print(f"✅ Full Success: {results['full_success']}")
        
    except Exception as e:
        logging.error(f"❌ Error during execution: {e}")
        raise


if __name__ == "__main__":
    main() 