from .wordle import Square, Wordle

TOTAL_GUESSES = 6
WORD_LENGTH = 5

def letter_emoji(letter):
	return f":regional_indicator_{letter}:"

def square_emoji(square: Square):
	emoji_name = {
		Square.FULL: "green_square",
		Square.PARTIAL: "yellow_square",
		Square.WRONG: "black_large_square"
	}[square]
	return f":{emoji_name}:"

def get_squares(actual: str, guess: str):
	squares = [Square.WRONG] * WORD_LENGTH
	# first go through the fully correct guesses
	for i, chars in enumerate(zip(actual, guess)):
		a, g = chars
		if a == g:
			squares[i] = Square.FULL
	# next, partial guesses
	# needs to be separate loop due to dupe chars
	for i, chars in enumerate(zip(actual, guess)):
		a, g = chars
		if a != g:
			# if actual != guess, scan for square to assign partial guess (*must* not already be a full or partial guess)
			for j, c in enumerate(guess):
				if c == a and squares[j] == Square.WRONG:
					squares[j] = Square.PARTIAL
					break
	return squares

def wordle_message(wordle: Wordle):
	message = []
	ended = False
	for guess in wordle.guesses:
		
		for letter in guess:
			if letter in wordle.remaining:
				wordle.remaining.remove(letter)
		
		squares = get_squares(wordle.actual, guess)
		
		squares_str = " ".join(str(square_emoji(square)) for square in squares)
		letters_str = " ".join(str(letter_emoji(letter)) for letter in guess)
		message.extend([letters_str, squares_str])
		
		if all(square == Square.FULL for square in squares):
			message.append(f"You won in {len(wordle.guesses)}!")
			ended = True
	
	if len(wordle.guesses) == TOTAL_GUESSES and not ended:
		message.append("You lost!")
		message.append(f"The word was {wordle.actual!r}")
		ended = True
	if not ended:
		message.append(f"Guesses Left: {TOTAL_GUESSES-len(wordle.guesses)}")
		message.append(
			f"Remaining Letters: {''.join(letter_emoji(letter) for letter in wordle.remaining)}"
		)
	return "\n".join(message), ended
